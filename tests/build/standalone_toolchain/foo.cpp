#include <stdio.h>

// Make sure we're not clobbering libc++ headers with libandroid_support.
#include <cmath>

// If std::strings don't work then there's really no point :)
#include <string>

void foo(const std::string& s) {
  // Using new makes sure we get libc++abi/libsupc++, using std::string makes
  // sure the STL works at all.
  std::string* copy = new std::string(s);
  printf("%s\n", copy->c_str());
  delete copy;
}

int main(int, char**) {
  foo("Hello, world!");
}
