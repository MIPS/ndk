#include <math.h>

#include <gtest/gtest.h>

// https://github.com/android-ndk/ndk/issues/204
// https://android-review.googlesource.com/276095
// libandroid_support's definition of the byte-order for doubles on armeabi was
// wrongly big endian rather than following the byte order of the ABI. This was
// due to a missing check for __ARM_EABI__ (a bug in the upstream FreeBSD libm
// source that bionic did not have because it has been updated since it was
// fixed).
TEST(log2, log2) {
  ASSERT_FLOAT_EQ(3.0, log2(8.0));
}
