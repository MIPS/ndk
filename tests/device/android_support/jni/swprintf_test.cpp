/*
 * Copyright (C) 2012 The Android Open Source Project
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

#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <wchar.h>

#include <gtest/gtest.h>

#include "fixed_in.h"

TEST(stdio, swprintf) {
  constexpr size_t nchars = 32;
  wchar_t buf[nchars];

  ASSERT_EQ(2, swprintf(buf, nchars, L"ab")) << strerror(errno);
  ASSERT_EQ(std::wstring(L"ab"), buf);
  ASSERT_EQ(5, swprintf(buf, nchars, L"%s", "abcde"));
  ASSERT_EQ(std::wstring(L"abcde"), buf);

  // Unlike swprintf(), swprintf() returns -1 in case of truncation
  // and doesn't necessarily zero-terminate the output!
  ASSERT_EQ(-1, swprintf(buf, 4, L"%s", "abcde"));

  const char kString[] = "Hello, World";
  ASSERT_EQ(12, swprintf(buf, nchars, L"%s", kString));
  ASSERT_EQ(std::wstring(L"Hello, World"), buf);
  ASSERT_EQ(12, swprintf(buf, 13, L"%s", kString));
  ASSERT_EQ(std::wstring(L"Hello, World"), buf);
}

// https://github.com/android-ndk/ndk/issues/437
TEST(stdio, swprintf_a) {
  FIXED_IN(__ANDROID_API_L__)

  constexpr size_t nchars = 32;
  wchar_t buf[nchars];

  ASSERT_EQ(20, swprintf(buf, nchars, L"%a", 3.1415926535));
  ASSERT_EQ(std::wstring(L"0x1.921fb54411744p+1"), buf);
}

TEST(stdio, swprintf_ls) {
  FIXED_IN(__ANDROID_API_L__)

  constexpr size_t nchars = 32;
  wchar_t buf[nchars];

  static const wchar_t kWideString[] = L"Hello\uff41 World";
  ASSERT_EQ(12, swprintf(buf, nchars, L"%ls", kWideString));
  ASSERT_EQ(std::wstring(kWideString), buf);
  ASSERT_EQ(12, swprintf(buf, 13, L"%ls", kWideString));
  ASSERT_EQ(std::wstring(kWideString), buf);
}

template <typename T>
static void CheckInfNan(int snprintf_fn(T*, size_t, const T*, ...),
                        int sscanf_fn(const T*, const T*, ...),
                        const T* fmt_string, const T* fmt, const T* fmt_plus,
                        const T* minus_inf, const T* inf_, const T* plus_inf,
                        const T* minus_nan, const T* nan_, const T* plus_nan) {
  T buf[BUFSIZ];
  float f;

  // NaN.

  snprintf_fn(buf, sizeof(buf), fmt, nanf(""));
  EXPECT_STREQ(nan_, buf) << fmt;
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f));
  EXPECT_TRUE(isnan(f));

  snprintf_fn(buf, sizeof(buf), fmt, -nanf(""));
  EXPECT_STREQ(minus_nan, buf) << fmt;
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f));
  EXPECT_TRUE(isnan(f));

  snprintf_fn(buf, sizeof(buf), fmt_plus, nanf(""));
  EXPECT_STREQ(plus_nan, buf) << fmt_plus;
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f));
  EXPECT_TRUE(isnan(f));

  snprintf_fn(buf, sizeof(buf), fmt_plus, -nanf(""));
  EXPECT_STREQ(minus_nan, buf) << fmt_plus;
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f));
  EXPECT_TRUE(isnan(f));

  // Inf.

  snprintf_fn(buf, sizeof(buf), fmt, HUGE_VALF);
  EXPECT_STREQ(inf_, buf) << fmt;
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f));
  EXPECT_EQ(HUGE_VALF, f);

  snprintf_fn(buf, sizeof(buf), fmt, -HUGE_VALF);
  EXPECT_STREQ(minus_inf, buf) << fmt;
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f));
  EXPECT_EQ(-HUGE_VALF, f);

  snprintf_fn(buf, sizeof(buf), fmt_plus, HUGE_VALF);
  EXPECT_STREQ(plus_inf, buf) << fmt_plus;
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f));
  EXPECT_EQ(HUGE_VALF, f);

  snprintf_fn(buf, sizeof(buf), fmt_plus, -HUGE_VALF);
  EXPECT_STREQ(minus_inf, buf) << fmt_plus;
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f));
  EXPECT_EQ(-HUGE_VALF, f);

  // Check case-insensitivity.
  snprintf_fn(buf, sizeof(buf), fmt_string, "[InFiNiTy]");
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f)) << buf;
  EXPECT_EQ(HUGE_VALF, f);
  snprintf_fn(buf, sizeof(buf), fmt_string, "[NaN]");
  EXPECT_EQ(1, sscanf_fn(buf, fmt, &f)) << buf;
  EXPECT_TRUE(isnan(f));
}

TEST(STDIO_TEST, swprintf_swscanf_inf_nan) {
  FIXED_IN(__ANDROID_API_O__)

  CheckInfNan(swprintf, swscanf, L"%s",
              L"[%a]", L"[%+a]",
              L"[-inf]", L"[inf]", L"[+inf]",
              L"[-nan]", L"[nan]", L"[+nan]");
  CheckInfNan(swprintf, swscanf, L"%s",
              L"[%A]", L"[%+A]",
              L"[-INF]", L"[INF]", L"[+INF]",
              L"[-NAN]", L"[NAN]", L"[+NAN]");
  CheckInfNan(swprintf, swscanf, L"%s",
              L"[%e]", L"[%+e]",
              L"[-inf]", L"[inf]", L"[+inf]",
              L"[-nan]", L"[nan]", L"[+nan]");
  CheckInfNan(swprintf, swscanf, L"%s",
              L"[%E]", L"[%+E]",
              L"[-INF]", L"[INF]", L"[+INF]",
              L"[-NAN]", L"[NAN]", L"[+NAN]");
  CheckInfNan(swprintf, swscanf, L"%s",
              L"[%f]", L"[%+f]",
              L"[-inf]", L"[inf]", L"[+inf]",
              L"[-nan]", L"[nan]", L"[+nan]");
  CheckInfNan(swprintf, swscanf, L"%s",
              L"[%F]", L"[%+F]",
              L"[-INF]", L"[INF]", L"[+INF]",
              L"[-NAN]", L"[NAN]", L"[+NAN]");
  CheckInfNan(swprintf, swscanf, L"%s",
              L"[%g]", L"[%+g]",
              L"[-inf]", L"[inf]", L"[+inf]",
              L"[-nan]", L"[nan]", L"[+nan]");
  CheckInfNan(swprintf, swscanf, L"%s",
              L"[%G]", L"[%+G]",
              L"[-INF]", L"[INF]", L"[+INF]",
              L"[-NAN]", L"[NAN]", L"[+NAN]");
}
