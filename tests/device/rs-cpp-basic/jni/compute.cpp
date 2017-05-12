/*
 * Copyright (C) 2016 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#if __clang__ && __has_include(<ftw.h>)
// The deprecated headers don't have this.
#define USE_FTW
#include <ftw.h>
#endif

#include <stdio.h>
#include <stdlib.h>

#include <string>

#include "RenderScript.h"
#include "ScriptC_mono.h"

#ifdef USE_FTW
int _remove_callback(const char* fpath, const struct stat* sb, int typeflag,
                     struct FTW* ftwbuf) {
  int rv = remove(fpath);
  if (rv == -1) {
    perror("remove");
  }

  return rv;
}

int remove_directory(const char* path) {
  return nftw(path, _remove_callback, 64, FTW_DEPTH | FTW_PHYS);
}
#else
int remove_directory(const char* path) {
  std::string cmd("rm -r ");
  cmd += path;
  int rv = system(cmd.c_str());
  if (rv == -1) {
    perror("system");
  }

  return rv;
}
#endif  // USE_FTW

class ScopedTempDir {
 public:
  ScopedTempDir(const std::string& base_temp_dir) : temp_dir_(base_temp_dir) {
    temp_dir_ += "/rs-cache-XXXXXX";
    if (mkdtemp(&temp_dir_[0]) == NULL) {
      perror("mkdtemp");
      abort();
    }
  }

  ~ScopedTempDir() {
      remove_directory(temp_dir_.c_str());
  }

  const std::string& path() const {
      return temp_dir_;
  }

 private:
  std::string temp_dir_;
};

int test_compute() {
  bool failed = false;

  {
    sp<RS> rs = new RS();
    printf("New RS %p\n", rs.get());

    // only legitimate because this is a standalone executable
    ScopedTempDir temp_dir("/data/local/tmp");
    bool r = rs->init(temp_dir.path().c_str());
    printf("Init returned %i\n", r);

    sp<const Element> e = Element::RGBA_8888(rs);
    printf("Element %p\n", e.get());

    Type::Builder tb(rs, e);
    tb.setX(128);
    tb.setY(128);
    sp<const Type> t = tb.create();
    printf("Type %p\n", t.get());

    sp<Allocation> a1 = Allocation::createSized(rs, e, 1000);
    printf("Allocation %p\n", a1.get());

    sp<Allocation> ain = Allocation::createTyped(rs, t);
    sp<Allocation> aout = Allocation::createTyped(rs, t);
    printf("Allocation %p %p\n", ain.get(), aout.get());

    sp<ScriptC_mono> sc = new ScriptC_mono(rs);
    printf("new script\n");

    sc->set_alloc(a1);
    sc->set_elem(e);
    sc->set_type(t);
    sc->set_script(sc);
    sc->set_script(nullptr);
    sp<const Sampler> samp = Sampler::CLAMP_NEAREST(rs);
    sc->set_sampler(samp);

    // We read back the status from the script-side via a "failed" allocation.
    sp<const Element> failed_e = Element::BOOLEAN(rs);
    Type::Builder failed_tb(rs, failed_e);
    failed_tb.setX(1);
    sp<const Type> failed_t = failed_tb.create();
    sp<Allocation> failed_alloc = Allocation::createTyped(rs, failed_t);

    failed_alloc->copy1DRangeFrom(0, failed_t->getCount(), &failed);
    sc->bind_failed(failed_alloc);

    uint32_t* buf = new uint32_t[t->getCount()];
    for (uint32_t ct = 0; ct < t->getCount(); ct++) {
      buf[ct] = ct | (ct << 16);
    }
    ain->copy1DRangeFrom(0, t->getCount(), buf);
    delete[] buf;

    sc->forEach_root(ain, aout);

    sc->invoke_foo(99, 3.1f);
    sc->set_g_f(39.9f);
    sc->set_g_i(-14);
    sc->invoke_foo(99, 3.1f);
    printf("for each done\n");

    sc->invoke_bar(47, -3, 'c', -7, 14, -8);

    // Verify a simple kernel.
    {
      static const uint32_t xDim = 7;
      static const uint32_t yDim = 7;
      sp<const Element> e = Element::I32(rs);
      Type::Builder tb(rs, e);
      tb.setX(xDim);
      tb.setY(yDim);
      sp<const Type> t = tb.create();
      sp<Allocation> kern1_in = Allocation::createTyped(rs, t);
      sp<Allocation> kern1_out = Allocation::createTyped(rs, t);

      int* buf = new int[t->getCount()];
      for (uint32_t ct = 0; ct < t->getCount(); ct++) {
        buf[ct] = 5;
      }
      kern1_in->copy2DRangeFrom(0, 0, xDim, yDim, buf);
      delete[] buf;

      sc->forEach_kern1(kern1_in, kern1_out);
      sc->forEach_verify_kern1(kern1_out);

      rs->finish();
      failed_alloc->copy1DTo(&failed);
    }
  }

  return failed;
}

int main() {
  bool failed = test_compute();

  if (failed) {
    printf("TEST FAILED!\n");
  } else {
    printf("TEST PASSED!\n");
  }

  return failed;
}
