#include <dlfcn.h>
#include <stdlib.h>

#include <iostream>

typedef bool (*test_func)();

void *load_library(const char *name) {
  void *lib = dlopen(name, RTLD_NOW);
  if (lib == nullptr) {
    std::cerr << dlerror() << std::endl;
    abort();
  }
  return lib;
}

test_func load_func(void *lib, const char *name) {
  test_func sym = reinterpret_cast<test_func>(dlsym(lib, name));
  if (sym == nullptr) {
    std::cerr << dlerror() << std::endl;
    abort();
  }
  return sym;
}

int main(int argc, char**) {
  // Explicitly loading libtypes.so before libtypestest.so so the type_infos it
  // contains are resolved with RTLD_LOCAL, which causes the address-only
  // type_info comparison to fail.
  load_library("libtypes.so");

  void *libtest = load_library("libtypestest.so");
  test_func do_test = load_func(libtest, "do_test");
  if (!do_test()) {
    std::cout << "do_test() failed!" << std::endl;
    return EXIT_FAILURE;
  }

  std::cout << "do_test() passed!" << std::endl;
  return EXIT_SUCCESS;
}
