#include <limits.h>
#include <stddef.h>
#include <wchar.h>

#include <gtest/gtest.h>

namespace {

const char* to_cstr(const wchar_t* wcs) {
    static char buffer[256];
    size_t n;
    for (n = 0; n + 1U < sizeof(buffer); ++n) {
        wchar_t ch = wcs[n];
        if (!ch)
            break;
        buffer[n] = (ch < 128) ? ch : '@';
    }
    buffer[n] = '\0';
    return buffer;
}

#define ARRAY_SIZE(x)  (sizeof(x) / sizeof(x[0]))

}

TEST(wchar, wchar_limits) {
  ASSERT_LT(WCHAR_MIN, WCHAR_MAX);
}

TEST(wchar, wcschr) {
  static const wchar_t kString[] = L"abcda";
  ASSERT_EQ(kString + 0, wcschr(kString, L'a'));
  ASSERT_EQ(kString + 1, wcschr(kString, L'b'));
  ASSERT_EQ(kString + 2, wcschr(kString, L'c'));
  ASSERT_EQ(kString + 3, wcschr(kString, L'd'));
  ASSERT_FALSE(wcschr(kString, L'e'));
  ASSERT_EQ(kString + 5, wcschr(kString, L'\0'));
}

TEST(wchar, wcsrchr) {
  static const wchar_t kString[] = L"abcda";
  ASSERT_EQ(kString + 4, wcsrchr(kString, L'a'));
  ASSERT_EQ(kString + 1, wcsrchr(kString, L'b'));
  ASSERT_EQ(kString + 2, wcsrchr(kString, L'c'));
  ASSERT_EQ(kString + 3, wcsrchr(kString, L'd'));
  ASSERT_FALSE(wcsrchr(kString, L'e'));
  ASSERT_EQ(kString + 5, wcsrchr(kString, L'\0'));
}

TEST(wchar, wcstof) {
    static const struct {
        const wchar_t* input;
        float expected;
        int expected_len;
    } kData[] = {
        { L"123", 123., 3 },
        { L"123#", 123., 3 },
        { L"   123 45", 123., 6 },
        { L"0.2", 0.2, 3 },
        { L"-0.2", -0.2, 4 },
        { L"-3.1415926535", -3.1415926535, 13 },
#if __ANDROID_API__ >= __ANDROID_API_L__
        { L"+1e+100", static_cast<float>(1e100), 7 },
        { L"0x10000.80", 65536.50, 10 },
#endif
    };
    for (size_t n = 0; n < ARRAY_SIZE(kData); ++n) {
        const char* text = to_cstr(kData[n].input);
        wchar_t* end;
        ASSERT_EQ(kData[n].expected, wcstof(kData[n].input, &end)) << text;
        ASSERT_EQ(kData[n].expected_len, (int)(end - kData[n].input)) << text;
    }
}

TEST(wchar, wcstod) {
    static const struct {
        const wchar_t* input;
        double expected;
        int expected_len;
    } kData[] = {
        { L"123", 123., 3 },
        { L"123#", 123., 3 },
        { L"   123 45", 123., 6 },
        { L"0.2", 0.2, 3 },
        { L"-0.2", -0.2, 4 },
        { L"-3.1415926535", -3.1415926535, 13 },
        { L"+1e+100", 1e100, 7 },
#if __ANDROID_API__ >= __ANDROID_API_L__
        { L"0x10000.80", 65536.50, 10 },
        { L"1.e60", 1e60, 5 },
#endif
    };
    for (size_t n = 0; n < ARRAY_SIZE(kData); ++n) {
        const char* text = to_cstr(kData[n].input);
        wchar_t* end;
        ASSERT_EQ(kData[n].expected, wcstod(kData[n].input, &end)) << text;
        ASSERT_EQ(kData[n].expected_len, (int)(end - kData[n].input)) << text;
    }
}

TEST(wchar, wcstold) {
    static const struct {
        const wchar_t* input;
        long double expected;
        int expected_len;
    } kData[] = {
        { L"123", 123., 3 },
        { L"123#", 123., 3 },
        { L"   123 45", 123., 6 },
        { L"0.2", 0.2L, 3 },
        { L"-0.2", -0.2L, 4 },
        { L"-3.1415926535", -3.1415926535L, 13 },
        { L"+1e+100", 1e100L, 7 },
#if __ANDROID_API__ >= __ANDROID_API_L__
        { L"0x10000.80", 65536.50L, 10 },
        { L"+1.e+100", 1e100L, 8 },
#endif
    };
    for (size_t n = 0; n < ARRAY_SIZE(kData); ++n) {
        const char* text = to_cstr(kData[n].input);
        wchar_t* end;
        ASSERT_EQ(kData[n].expected, wcstold(kData[n].input, &end)) << text;
        ASSERT_EQ(kData[n].expected_len, (int)(end - kData[n].input)) << text;
    }
}

TEST(wchar, wcstol) {
    static const struct {
        const wchar_t* input;
        int base;
        long expected;
        int expected_len;
    } kData[] = {
        { L"123", 10, 123, 3 },
        { L"123#", 10, 123, 3 },
        { L"01000", 0, 512, 5 },
        { L"   123 45", 0, 123, 6 },
        { L"  -123", 0, -123, 6 },
        { L"0x10000", 0, 65536, 7 },
        { L"12222222222222222222222222222222222", 10, LONG_MAX, 35 },
        { L"-12222222222222222222222222222222222", 10, LONG_MIN, 36 },
    };
    for (size_t n = 0; n < ARRAY_SIZE(kData); ++n) {
        const char* text = to_cstr(kData[n].input);
        wchar_t* end;
        ASSERT_EQ(kData[n].expected, wcstol(kData[n].input, &end, kData[n].base)) << text;
        ASSERT_EQ(kData[n].expected_len, (int)(end - kData[n].input)) << text;
    }
}

TEST(wchar, wcstoul) {
    static const struct {
        const wchar_t* input;
        int base;
        unsigned long expected;
        int expected_len;
    } kData[] = {
        { L"123", 10, 123, 3 },
        { L"123#", 10, 123, 3 },
        { L"01000", 0, 512, 5 },
        { L"   123 45", 0, 123, 6 },
        { L"  -123", 0, ULONG_MAX - 123 + 1, 6 },
        { L"0x10000", 0, 65536, 7 },
        { L"12222222222222222222222222222222222", 10, ULONG_MAX, 35 },
        { L"-1", 10, ULONG_MAX, 2 },
    };
    for (size_t n = 0; n < ARRAY_SIZE(kData); ++n) {
        const char* text = to_cstr(kData[n].input);
        wchar_t* end;
        ASSERT_EQ(kData[n].expected, wcstoul(kData[n].input, &end, kData[n].base)) << text;
        ASSERT_EQ(kData[n].expected_len, (int)(end - kData[n].input)) << text;
    }
}

TEST(wchar, wcstoll) {
    static const struct {
        const wchar_t* input;
        int base;
        long long expected;
        int expected_len;
    } kData[] = {
        { L"123", 10, 123, 3 },
        { L"123#", 10, 123, 3 },
        { L"01000", 0, 512, 5 },
        { L"   123 45", 0, 123, 6 },
        { L"  -123", 0, -123, 6 },
        { L"0x10000", 0, 65536, 7 },
        { L"12222222222222222222222222222222222", 10, LLONG_MAX, 35 },
        { L"-12222222222222222222222222222222222", 10, LLONG_MIN, 36 },
    };
    for (size_t n = 0; n < ARRAY_SIZE(kData); ++n) {
        const char* text = to_cstr(kData[n].input);
        wchar_t* end;
        ASSERT_EQ(kData[n].expected, wcstoll(kData[n].input, &end, kData[n].base)) << text;
        ASSERT_EQ(kData[n].expected_len, (int)(end - kData[n].input)) << text;
    }
}

TEST(wchar, wcstoull) {
    static const struct {
        const wchar_t* input;
        int base;
        unsigned long long expected;
        int expected_len;
    } kData[] = {
        { L"123", 10, 123, 3 },
        { L"123#", 10, 123, 3 },
        { L"01000", 0, 512, 5 },
        { L"   123 45", 0, 123, 6 },
        { L"  -123", 0, ULLONG_MAX - 123 + 1, 6 },
        { L"0x10000", 0, 65536, 7 },
        { L"12222222222222222222222222222222222", 10, ULLONG_MAX, 35 },
        { L"-1", 10, ULLONG_MAX, 2 },
    };
    for (size_t n = 0; n < ARRAY_SIZE(kData); ++n) {
        const char* text = to_cstr(kData[n].input);
        wchar_t* end;
        ASSERT_EQ(kData[n].expected, wcstoull(kData[n].input, &end, kData[n].base)) << text;
        ASSERT_EQ(kData[n].expected_len, (int)(end - kData[n].input)) << text;
    }
}
