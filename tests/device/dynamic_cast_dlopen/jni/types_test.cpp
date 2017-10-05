#include "types.h"

extern "C" bool do_test() {
  MyTypeImpl impl;
  MyType* base = &impl;
  return dynamic_cast<MyTypeImpl*>(base) != nullptr;
}
