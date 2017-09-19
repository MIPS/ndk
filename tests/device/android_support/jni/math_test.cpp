/*
 * Copyright (C) 2017 The Android Open Source Project
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

#include <math.h>

// https://github.com/android-ndk/ndk/issues/502
TEST(math, frexp) {
  int exp;
  double dr = frexp(1024.0, &exp);
  ASSERT_DOUBLE_EQ(1024.0, scalbn(dr, exp));
}

// https://github.com/android-ndk/ndk/issues/502
TEST(math, frexpf) {
  int exp;
  float fr = frexpf(1024.0f, &exp);
  ASSERT_FLOAT_EQ(1024.0f, scalbnf(fr, exp));
}

// https://github.com/android-ndk/ndk/issues/502
TEST(math, frexpl) {
  int exp;
  long double ldr = frexpl(1024.0L, &exp);
  ASSERT_DOUBLE_EQ(1024.0L, scalbnl(ldr, exp));
}

// https://github.com/android-ndk/ndk/issues/502
TEST(math, log2f) {
  ASSERT_FLOAT_EQ(12.0f, log2f(4096.0f));
}
