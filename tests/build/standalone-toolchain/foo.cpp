#include <stdio.h>

#include <string>

void foo(const std::string& s) {
  // Using new makes sure we get libc++abi/libsupc++, using std::string makes
  // sure the STL works at all.
  std::string* copy = new std::string(s);
  printf("%s\n", copy->c_str());
  delete copy;
}
