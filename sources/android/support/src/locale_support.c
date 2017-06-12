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
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <wctype.h>

// Contains an implementation of all locale-specific functions (those
// ending in _l, like strcoll_l()), as simple wrapper to the non-locale
// specific ones for now.
//
// That's because Android's C library doesn't support locales. Or more
// specifically, only supports the "C" one.
//
// TODO(digit): Write a more complete implementation that uses JNI to
//              invoke the platform APIs to implement proper handling.
//

#if __ANDROID_API__ < 21

int vasprintf_l(char** strp, locale_t l, const char* fmt, va_list args) {
    // Ignore locale.
    return vasprintf(strp, fmt, args);
}

int asprintf_l(char** strp, locale_t locale, const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int result = vasprintf_l(strp, locale, fmt, args);
    va_end(args);
    return result;
}

int vsprintf_l(char* str, locale_t l, const char* fmt, va_list args) {
    // Ignore locale.
    return vsprintf(str, fmt, args);
}

int sprintf_l(char* str, locale_t l, const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int result = vsprintf_l(str, l, fmt, args);
    va_end(args);
    return result;
}

int vsnprintf_l(char* str, size_t size, locale_t l, const char* fmt, va_list args) {
    return vsnprintf(str, size, fmt, args);
}

int snprintf_l(char* str, size_t size, locale_t l, const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  int result = vsnprintf_l(str, size, l, fmt, args);
  va_end(args);
  return result;
}

int vsscanf_l(const char* str, locale_t l, const char* fmt, va_list args) {
    return vsscanf(str, fmt, args);
}

int sscanf_l(const char* str, locale_t l, const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int result = vsscanf_l(str, l, fmt, args);
    va_end(args);
    return result;
}

long double strtold_l (const char *nptr, char **endptr, locale_t loc) {
    return strtold(nptr, endptr);
}

long long strtoll_l(const char *nptr, char **endptr, int base, locale_t loc) {
    return strtoll(nptr, endptr, base);
}

unsigned long long strtoull_l(const char *nptr, char **endptr, int base, locale_t loc) {
    return strtoull(nptr, endptr, base);
}
#endif // __ANDROID_API__ < 21

#if __ANDROID_API__ < 26
long strtol_l(const char *nptr, char **endptr, int base, locale_t loc) {
    return strtol(nptr, endptr, base);
}

unsigned long strtoul_l(const char *nptr, char **endptr, int base, locale_t loc) {
    return strtoul(nptr, endptr, base);
}

double strtod_l(const char* nptr, char** endptr, locale_t __unused locale) {
  return strtod(nptr, endptr);
}

float strtof_l(const char* nptr, char** endptr, locale_t __unused locale) {
  return strtof(nptr, endptr);
}
#endif // __ANDROID_API__ < 26
