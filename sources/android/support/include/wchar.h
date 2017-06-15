/*
  Copyright (C) 2005-2012 Rich Felker

  Permission is hereby granted, free of charge, to any person obtaining
  a copy of this software and associated documentation files (the
  "Software"), to deal in the Software without restriction, including
  without limitation the rights to use, copy, modify, merge, publish,
  distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so, subject to
  the following conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

  Modified in 2013 for the Android Open Source Project.
 */
#ifndef NDK_ANDROID_SUPPORT_WCHAR_H
#define NDK_ANDROID_SUPPORT_WCHAR_H

#include_next <wchar.h>

__BEGIN_DECLS

#if __ANDROID_API__ < __ANDROID_API_L__

size_t mbsnrtowcs(wchar_t*, const char**, size_t, size_t, mbstate_t*);
int vswprintf(wchar_t*, size_t, const wchar_t*, va_list);
size_t wcsnrtombs(char*, const wchar_t**, size_t, size_t, mbstate_t*);
float wcstof(const wchar_t*, wchar_t**);
long long wcstoll(const wchar_t*, wchar_t**, int);
long double wcstold(const wchar_t*, wchar_t**);
unsigned long long wcstoull(const wchar_t*, wchar_t**, int);

size_t wcslcat(wchar_t*, const wchar_t*, size_t);
size_t wcslcpy(wchar_t*, const wchar_t*, size_t);

intmax_t wcstoimax(const wchar_t* nptr, wchar_t** endptr, int base);
uintmax_t wcstoumax(const wchar_t* nptr, wchar_t** endptr, int base);

size_t wcsnlen(const wchar_t*, size_t);

#endif /* __ANDROID_API__ < __ANDROID_API_L__ */

#if __ANDROID_API__ < __ANDROID_API_M__

int wcscasecmp_l(const wchar_t*, const wchar_t*, locale_t);
int wcsncasecmp_l(const wchar_t*, const wchar_t*, size_t, locale_t);

#endif /* __ANDROID_API__ < __ANDROID_API_L__ */

__END_DECLS

#endif  // NDK_ANDROID_SUPPORT_WCHAR_H
