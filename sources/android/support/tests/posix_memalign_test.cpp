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
