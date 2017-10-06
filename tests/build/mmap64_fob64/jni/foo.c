#include <sys/mman.h>

int main(int argc, char** argv) {
  mmap(0, 0, 0, 0, 0, 0);
  return 0;
}
