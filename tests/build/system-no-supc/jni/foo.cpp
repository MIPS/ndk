#include <sys/types.h>

extern "C" void* __cxa_allocate_exception(size_t thrown_size) noexcept;

void* foo(size_t thrown_size) noexcept {
  return __cxa_allocate_exception(thrown_size);
}
