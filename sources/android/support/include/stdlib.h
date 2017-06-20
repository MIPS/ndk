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
#ifndef NDK_ANDROID_SUPPORT_STDLIB_H
#define NDK_ANDROID_SUPPORT_STDLIB_H

#include_next <stdlib.h>
#include <xlocale.h>

__BEGIN_DECLS

#if __ANDROID_API__ < 16
int posix_memalign(void** memptr, size_t alignment, size_t size);
#endif

// These APIs made it in to L.
#if __ANDROID_API__ < 21

void _Exit(int);

long double strtold(const char*, char**);
long double strtold_l(const char* nptr, char** endptr, locale_t loc);
long long strtoll_l(const char* nptr, char** endptr, int base, locale_t loc);
unsigned long long strtoull_l(const char* nptr, char** endptr, int base,
                              locale_t loc);

int mbtowc(wchar_t* pwc, const char* pmb, size_t n);

#if __ISO_C_VISIBLE >= 2011 || __cplusplus >= 201103L
int at_quick_exit(void (*)(void));
void quick_exit(int) __noreturn;
#endif

#endif // __ANDROID_API__ < 21

// These APIs made it in to O.
#if __ANDROID_API__ < 26
double strtod_l(const char* nptr, char** endptr, locale_t locale);
float strtof_l(const char* nptr, char** endptr, locale_t locale);
long strtol_l(const char* nptr, char** endptr, int base, locale_t locale);
unsigned long strtoul_l(const char* nptr, char** endptr, int base,
                        locale_t locale);
#endif // __ANDROID_API__ < 26

__END_DECLS

#endif  // NDK_ANDROID_SUPPORT_STDLIB_H
