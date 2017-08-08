/*
 * Copyright (C) 2012 The Android Open Source Project
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *  * Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
 * OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

#include <gtest/gtest.h>

TEST(stdlib, posix_memalign_sweep) {
  void* ptr;

  // These should all fail.
  for (size_t align = 0; align < sizeof(long); align++) {
    ASSERT_EQ(EINVAL, posix_memalign(&ptr, align, 256))
        << "Unexpected value at align " << align;
  }

  // Verify powers of 2 up to 2048 allocate, and verify that all other
  // alignment values between the powers of 2 fail.
  size_t last_align = sizeof(long);
  for (size_t align = sizeof(long); align <= 2048; align <<= 1) {
    // Try all of the non power of 2 values from the last until this value.
    for (size_t fail_align = last_align + 1; fail_align < align; fail_align++) {
      ASSERT_EQ(EINVAL, posix_memalign(&ptr, fail_align, 256))
          << "Unexpected success at align " << fail_align;
    }
    ASSERT_EQ(0, posix_memalign(&ptr, align, 256))
        << "Unexpected failure at align " << align;
    ASSERT_EQ(0U, reinterpret_cast<uintptr_t>(ptr) & (align - 1))
        << "Did not return a valid aligned ptr " << ptr << " expected alignment " << align;
    free(ptr);
    last_align = align;
  }
}

TEST(stdlib, posix_memalign_various_sizes) {
  std::vector<size_t> sizes{1, 4, 8, 256, 1024, 65000, 128000, 256000, 1000000};
  for (auto size : sizes) {
    void* ptr;
    ASSERT_EQ(0, posix_memalign(&ptr, 16, 1))
        << "posix_memalign failed at size " << size;
    ASSERT_EQ(0U, reinterpret_cast<uintptr_t>(ptr) & 0xf)
        << "Pointer not aligned at size " << size << " ptr " << ptr;
    free(ptr);
  }
}
