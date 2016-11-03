/*
 * Copyright (C) 2016 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef NDK_ANDROID_SUPPORT_FENV_H
#define NDK_ANDROID_SUPPORT_FENV_H

#include <sys/cdefs.h>

/* Before android-21, only x86 had a working fenv implementation. */
#if __ANDROID_API__ < 21                                                       \
    && (defined(__arm__) || (defined(__mips__) && !defined(__LP64__)))

#include <machine/fenv.h>
#include <sys/cdefs.h>

__BEGIN_DECLS

/* Default floating-point environment. */
extern const fenv_t __fe_dfl_env;
#define FE_DFL_ENV (&__fe_dfl_env)

int fegetenv(fenv_t* __envp);
int fesetenv(const fenv_t* __envp);
int feclearexcept(int __excepts);
int fegetexceptflag(fexcept_t* __flagp, int __excepts);
int fesetexceptflag(const fexcept_t* __flagp, int __excepts);
int feraiseexcept(int __excepts);
int fetestexcept(int __excepts);
int fegetround(void);
int fesetround(int __round);
int feholdexcept(fenv_t* __envp);
int feupdateenv(const fenv_t* __envp);
int feenableexcept(int __mask);
int fedisableexcept(int __mask);
int fegetexcept(void);

__END_DECLS

#else
#include_next <fenv.h>
#endif

#endif /* NDK_ANDROID_SUPPORT_FENV_H */
