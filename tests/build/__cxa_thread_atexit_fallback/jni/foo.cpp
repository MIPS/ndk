#include <iostream>

struct Foo {
  ~Foo() {
    std::cout << "~Foo()" << std::endl;
  }
};

int main() {
  thread_local Foo foo;
  return 0;
}
