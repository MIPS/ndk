/*
 * Copyright (C) 2013 The Android Open Source Project
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

intmax_t wcstoimax(const wchar_t* nptr, wchar_t** endptr, int base);
uintmax_t wcstoumax(const wchar_t* nptr, wchar_t** endptr, int base);

#endif /* __ANDROID_API__ < __ANDROID_API_L__ */

#if __ANDROID_API__ < __ANDROID_API_M__

int wcscasecmp_l(const wchar_t*, const wchar_t*, locale_t);
int wcsncasecmp_l(const wchar_t*, const wchar_t*, size_t, locale_t);

#endif /* __ANDROID_API__ < __ANDROID_API_L__ */

__END_DECLS

#endif
