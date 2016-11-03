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

#include <fenv.h>

#define _FPSCR_ENABLE_SHIFT 8
#define _FPSCR_ENABLE_MASK (FE_ALL_EXCEPT << _FPSCR_ENABLE_SHIFT)

#define _FPSCR_RMODE_SHIFT 22

int fegetenv(fenv_t* __envp) {
  fenv_t _fpscr;
#if !defined(__SOFTFP__)
  #if !defined(__thumb__) || defined(__thumb2__)
  __asm__ __volatile__("vmrs %0,fpscr" : "=r" (_fpscr));
  #else
   /* Switching from thumb1 to arm, do vmrs, then switch back */
  __asm__ __volatile__(
    ".balign 4           \n\t"
    "mov     ip, pc      \n\t"
    "bx      ip          \n\t"
    ".arm                \n\t"
    "vmrs    %0, fpscr   \n\t"
    "add     ip, pc, #1  \n\t"
    "bx      ip          \n\t"
    ".thumb              \n\t"
    : "=r" (_fpscr) : : "ip");
  #endif
#else
  _fpscr = 0;
#endif
  *__envp = _fpscr;
  return 0;
}

int fesetenv(const fenv_t* __envp) {
  fenv_t _fpscr = *__envp;
#if !defined(__SOFTFP__)
  #if !defined(__thumb__) || defined(__thumb2__)
  __asm__ __volatile__("vmsr fpscr,%0" : :"ri" (_fpscr));
  #else
   /* Switching from thumb1 to arm, do vmsr, then switch back */
  __asm__ __volatile__(
    ".balign 4           \n\t"
    "mov     ip, pc      \n\t"
    "bx      ip          \n\t"
    ".arm                \n\t"
    "vmsr    fpscr, %0   \n\t"
    "add     ip, pc, #1  \n\t"
    "bx      ip          \n\t"
    ".thumb              \n\t"
    : : "ri" (_fpscr) : "ip");
  #endif
#else
  _fpscr = _fpscr;
#endif
  return 0;
}

int feclearexcept(int __excepts) {
  fexcept_t __fpscr;
  fegetenv(&__fpscr);
  __fpscr &= ~__excepts;
  fesetenv(&__fpscr);
  return 0;
}

int fegetexceptflag(fexcept_t* __flagp, int __excepts) {
  fexcept_t __fpscr;
  fegetenv(&__fpscr);
  *__flagp = __fpscr & __excepts;
  return 0;
}

int fesetexceptflag(const fexcept_t* __flagp, int __excepts) {
  fexcept_t __fpscr;
  fegetenv(&__fpscr);
  __fpscr &= ~__excepts;
  __fpscr |= *__flagp & __excepts;
  fesetenv(&__fpscr);
  return 0;
}

int feraiseexcept(int __excepts) {
  fexcept_t __ex = __excepts;
  fesetexceptflag(&__ex, __excepts);
  return 0;
}

int fetestexcept(int __excepts) {
  fexcept_t __fpscr;
  fegetenv(&__fpscr);
  return (__fpscr & __excepts);
}

int fegetround(void) {
  fenv_t _fpscr;
  fegetenv(&_fpscr);
  return ((_fpscr >> _FPSCR_RMODE_SHIFT) & 0x3);
}

int fesetround(int __round) {
  fenv_t _fpscr;
  fegetenv(&_fpscr);
  _fpscr &= ~(0x3 << _FPSCR_RMODE_SHIFT);
  _fpscr |= (__round << _FPSCR_RMODE_SHIFT);
  fesetenv(&_fpscr);
  return 0;
}

int feholdexcept(fenv_t* __envp) {
  fenv_t __env;
  fegetenv(&__env);
  *__envp = __env;
  __env &= ~(FE_ALL_EXCEPT | _FPSCR_ENABLE_MASK);
  fesetenv(&__env);
  return 0;
}

int feupdateenv(const fenv_t* __envp) {
  fexcept_t __fpscr;
  fegetenv(&__fpscr);
  fesetenv(__envp);
  feraiseexcept(__fpscr & FE_ALL_EXCEPT);
  return 0;
}

int feenableexcept(int __mask) {
  fenv_t __old_fpscr, __new_fpscr;
  fegetenv(&__old_fpscr);
  __new_fpscr = __old_fpscr | (__mask & FE_ALL_EXCEPT) << _FPSCR_ENABLE_SHIFT;
  fesetenv(&__new_fpscr);
  return ((__old_fpscr >> _FPSCR_ENABLE_SHIFT) & FE_ALL_EXCEPT);
}

int fedisableexcept(int __mask) {
  fenv_t __old_fpscr, __new_fpscr;
  fegetenv(&__old_fpscr);
  __new_fpscr = __old_fpscr & ~((__mask & FE_ALL_EXCEPT) << _FPSCR_ENABLE_SHIFT);
  fesetenv(&__new_fpscr);
  return ((__old_fpscr >> _FPSCR_ENABLE_SHIFT) & FE_ALL_EXCEPT);
}

int fegetexcept(void) {
  fenv_t __fpscr;
  fegetenv(&__fpscr);
  return ((__fpscr & _FPSCR_ENABLE_MASK) >> _FPSCR_ENABLE_SHIFT);
}
