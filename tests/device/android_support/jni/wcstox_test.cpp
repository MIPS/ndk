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

#include <inttypes.h>
#include <math.h>
#include <wchar.h>

#include <limits>

#include <gtest/gtest.h>

#include "fixed_in.h"

template <typename T>
using WcsToIntFn = T (*)(const wchar_t*, wchar_t**, int);

template <typename T>
using WcsToFloatFn = T (*)(const wchar_t*, wchar_t**);

template <typename T>
void TestSingleWcsToFloat(WcsToFloatFn<T> fn, const wchar_t* str,
                          T expected_value, ptrdiff_t expected_len) {
  wchar_t* p;
  ASSERT_EQ(expected_value, fn(str, &p));
  ASSERT_EQ(expected_len, p - str);
}

template <typename T>
void TestWcsToFloat(WcsToFloatFn<T> fn) {
  TestSingleWcsToFloat(fn, L"123", static_cast<T>(123.0), 3);
  TestSingleWcsToFloat(fn, L"123#", static_cast<T>(123.0), 3);
  TestSingleWcsToFloat(fn, L"   123 45", static_cast<T>(123.0), 6);
  TestSingleWcsToFloat(fn, L"9.0", static_cast<T>(9.0), 3);
  TestSingleWcsToFloat(fn, L"-9.0", static_cast<T>(-9.0), 4);
  TestSingleWcsToFloat(fn, L" \t\v\f\r\n9.0", static_cast<T>(9.0), 9);
}

template <typename T>
void TestWcsToFloatHexFloats(WcsToFloatFn<T> fn) {
  TestSingleWcsToFloat(fn, L"0.9e1", static_cast<T>(9.0), 5);
  TestSingleWcsToFloat(fn, L"0x1.2p3", static_cast<T>(9.0), 7);
  TestSingleWcsToFloat(fn, L"+1e+100", static_cast<T>(1e100), 7);
  TestSingleWcsToFloat(fn, L"0x10000.80", static_cast<T>(65536.50), 10);
}

template <typename T>
void TestWcsToFloatInfNan(WcsToFloatFn<T> fn) {
  ASSERT_TRUE(isnan(fn(L"+nan", nullptr)));
  ASSERT_TRUE(isnan(fn(L"nan", nullptr)));
  ASSERT_TRUE(isnan(fn(L"-nan", nullptr)));

  ASSERT_TRUE(isnan(fn(L"+nan(0xff)", nullptr)));
  ASSERT_TRUE(isnan(fn(L"nan(0xff)", nullptr)));
  ASSERT_TRUE(isnan(fn(L"-nan(0xff)", nullptr)));

  wchar_t* p;
  ASSERT_TRUE(isnan(fn(L"+nanny", &p)));
  ASSERT_STREQ(L"ny", p);
  ASSERT_TRUE(isnan(fn(L"nanny", &p)));
  ASSERT_STREQ(L"ny", p);
  ASSERT_TRUE(isnan(fn(L"-nanny", &p)));
  ASSERT_STREQ(L"ny", p);

  ASSERT_EQ(0, fn(L"muppet", &p));
  ASSERT_STREQ(L"muppet", p);
  ASSERT_EQ(0, fn(L"  muppet", &p));
  ASSERT_STREQ(L"  muppet", p);

  ASSERT_EQ(std::numeric_limits<T>::infinity(), fn(L"+inf", nullptr));
  ASSERT_EQ(std::numeric_limits<T>::infinity(), fn(L"inf", nullptr));
  ASSERT_EQ(-std::numeric_limits<T>::infinity(), fn(L"-inf", nullptr));

  ASSERT_EQ(std::numeric_limits<T>::infinity(), fn(L"+infinity", nullptr));
  ASSERT_EQ(std::numeric_limits<T>::infinity(), fn(L"infinity", nullptr));
  ASSERT_EQ(-std::numeric_limits<T>::infinity(), fn(L"-infinity", nullptr));

  ASSERT_EQ(std::numeric_limits<T>::infinity(), fn(L"+infinitude", &p));
  ASSERT_STREQ(L"initude", p);
  ASSERT_EQ(std::numeric_limits<T>::infinity(), fn(L"infinitude", &p));
  ASSERT_STREQ(L"initude", p);
  ASSERT_EQ(-std::numeric_limits<T>::infinity(), fn(L"-infinitude", &p));
  ASSERT_STREQ(L"initude", p);

  // Check case-insensitivity.
  ASSERT_EQ(std::numeric_limits<T>::infinity(), fn(L"InFiNiTy", nullptr));
  ASSERT_TRUE(isnan(fn(L"NaN", nullptr)));
}

TEST(wchar, wcstof) {
  TestWcsToFloat(wcstof);
}

TEST(wchar, wcstof_hex_floats) {
  FIXED_IN(__ANDROID_API_O__)
  TestWcsToFloatHexFloats(wcstof);
}

TEST(wchar, wcstof_hex_inf_nan) {
  FIXED_IN(__ANDROID_API_O__)
  TestWcsToFloatInfNan(wcstof);
}

TEST(wchar, wcstod) {
  TestWcsToFloat(wcstod);
}

TEST(wchar, wcstod_hex_floats) {
  FIXED_IN(__ANDROID_API_O__)
  TestWcsToFloatHexFloats(wcstod);
}

TEST(wchar, wcstod_hex_inf_nan) {
  FIXED_IN(__ANDROID_API_O__)
  TestWcsToFloatInfNan(wcstod);
}

TEST(wchar, wcstold) {
  TestWcsToFloat(wcstold);
}

TEST(wchar, wcstold_hex_floats) {
  FIXED_IN(__ANDROID_API_O__)
  TestWcsToFloatHexFloats(wcstold);
}

TEST(wchar, wcstold_hex_inf_nan) {
  FIXED_IN(__ANDROID_API_O__)
  TestWcsToFloatInfNan(wcstold);
}

template <typename T>
void TestSingleWcsToInt(WcsToIntFn<T> fn, const wchar_t* str, int base,
                        T expected_value, ptrdiff_t expected_len) {
  wchar_t* p;
  ASSERT_EQ(expected_value, fn(str, &p, base));
  ASSERT_EQ(expected_len, p - str) << str;
}

template <typename T>
void TestWcsToInt(WcsToIntFn<T> fn) {
  TestSingleWcsToInt(fn, L"123", 10, static_cast<T>(123), 3);
  TestSingleWcsToInt(fn, L"123", 0, static_cast<T>(123), 3);
  TestSingleWcsToInt(fn, L"123#", 10, static_cast<T>(123), 3);
  TestSingleWcsToInt(fn, L"01000", 8, static_cast<T>(512), 5);
  TestSingleWcsToInt(fn, L"01000", 0, static_cast<T>(512), 5);
  TestSingleWcsToInt(fn, L"   123 45", 0, static_cast<T>(123), 6);
  TestSingleWcsToInt(fn, L"  -123", 0, static_cast<T>(-123), 6);
  TestSingleWcsToInt(fn, L"0x10000", 0, static_cast<T>(65536), 7);
}

template <typename T>
void TestWcsToIntLimits(WcsToIntFn<T> fn, const wchar_t* min_str,
                        const wchar_t* max_str) {
  if (std::is_signed<T>::value) {
    ASSERT_EQ(std::numeric_limits<T>::min(), fn(min_str, nullptr, 0)) << min_str;
  } else {
    // If the subject sequence begins with a <hyphen-minus>, the value resulting
    // from the conversion shall be negated.
    // http://pubs.opengroup.org/onlinepubs/9699919799/functions/strtoul.html
    ASSERT_EQ(std::numeric_limits<T>::max(), fn(min_str, nullptr, 0)) << min_str;
  }
  ASSERT_EQ(std::numeric_limits<T>::max(), fn(max_str, nullptr, 0)) << max_str;
}

TEST(wchar, wcstol) {
  TestWcsToInt(wcstol);
}

TEST(wchar, wcstol_limits) {
  if (sizeof(long) == 8) {
    TestWcsToIntLimits(wcstol, L"-9223372036854775809", L"9223372036854775808");
  } else {
    TestWcsToIntLimits(wcstol, L"-2147483649", L"2147483648");
  }
}

TEST(wchar, wcstoul) {
  TestWcsToInt(wcstoul);
}

TEST(wchar, wcstoul_limits) {
  if (sizeof(long) == 8) {
    TestWcsToIntLimits(wcstoul, L"-1", L"18446744073709551616");
  } else {
    TestWcsToIntLimits(wcstoul, L"-1", L"4294967296");
  }
}

TEST(wchar, wcstoll) {
  TestWcsToInt(wcstoll);
}

TEST(wchar, wcstoll_limits) {
  TestWcsToIntLimits(wcstoll, L"-9223372036854775809", L"9223372036854775808");
}

TEST(wchar, wcstoull) {
  TestWcsToInt(wcstoull);
}

TEST(wchar, wcstoull_limits) {
  TestWcsToIntLimits(wcstoull, L"-1", L"18446744073709551616");
}

TEST(wchar, wcstoimax) {
  TestWcsToInt(wcstoimax);
}

TEST(wchar, wcstoimax_limits) {
  TestWcsToIntLimits(wcstoimax, L"-9223372036854775809",
                     L"9223372036854775808");
}

TEST(wchar, wcstoumax) {
  TestWcsToInt(wcstoumax);
}

TEST(wchar, wcstoumax_limits) {
  TestWcsToIntLimits(wcstoumax, L"-1", L"18446744073709551616");
}
