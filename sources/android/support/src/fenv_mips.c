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

#define _FCSR_CAUSE_SHIFT  10
#define _ENABLE_SHIFT 5
#define _FCSR_ENABLE_MASK (FE_ALL_EXCEPT << _ENABLE_SHIFT)

#define _FCSR_RMODE_SHIFT 0
#define _FCSR_RMASK       0x3

int fegetenv(fenv_t* __envp) {
   fenv_t _fcsr = 0;
#ifdef  __mips_hard_float
   __asm__ __volatile__("cfc1 %0,$31" : "=r" (_fcsr));
#endif
   *__envp = _fcsr;
   return 0;
}

int fesetenv(const fenv_t* __envp) {
  fenv_t _fcsr = *__envp;
#ifdef  __mips_hard_float
  __asm__ __volatile__("ctc1 %0,$31" : : "r" (_fcsr));
#endif
  return 0;
}

int feclearexcept(int __excepts) {
  fexcept_t __fcsr;
  fegetenv(&__fcsr);
  __excepts &= FE_ALL_EXCEPT;
  __fcsr &= ~(__excepts | (__excepts << _FCSR_CAUSE_SHIFT));
  fesetenv(&__fcsr);
  return 0;
}

int fegetexceptflag(fexcept_t* __flagp, int __excepts) {
  fexcept_t __fcsr;
  fegetenv(&__fcsr);
  *__flagp = __fcsr & __excepts & FE_ALL_EXCEPT;
  return 0;
}

int fesetexceptflag(const fexcept_t* __flagp, int __excepts) {
  fexcept_t __fcsr;
  fegetenv(&__fcsr);
  /* Ensure that flags are all legal */
  __excepts &= FE_ALL_EXCEPT;
  __fcsr &= ~__excepts;
  __fcsr |= *__flagp & __excepts;
  fesetenv(&__fcsr);
  return 0;
}

int feraiseexcept(int __excepts) {
  fexcept_t __fcsr;
  fegetenv(&__fcsr);
  /* Ensure that flags are all legal */
  __excepts &= FE_ALL_EXCEPT;
  /* Cause bit needs to be set as well for generating the exception*/
  __fcsr |= __excepts | (__excepts << _FCSR_CAUSE_SHIFT);
  fesetenv(&__fcsr);
  return 0;
}

int fetestexcept(int __excepts) {
  fexcept_t __FCSR;
  fegetenv(&__FCSR);
  return (__FCSR & __excepts & FE_ALL_EXCEPT);
}

int fegetround(void) {
  fenv_t _fcsr;
  fegetenv(&_fcsr);
  return (_fcsr & _FCSR_RMASK);
}

int fesetround(int __round) {
  fenv_t _fcsr;
  fegetenv(&_fcsr);
  _fcsr &= ~_FCSR_RMASK;
  _fcsr |= (__round & _FCSR_RMASK ) ;
  fesetenv(&_fcsr);
  return 0;
}

int feholdexcept(fenv_t* __envp) {
  fenv_t __env;
  fegetenv(&__env);
  *__envp = __env;
  __env &= ~(FE_ALL_EXCEPT | _FCSR_ENABLE_MASK);
  fesetenv(&__env);
  return 0;
}

int feupdateenv(const fenv_t* __envp) {
  fexcept_t __fcsr;
  fegetenv(&__fcsr);
  fesetenv(__envp);
  feraiseexcept(__fcsr & FE_ALL_EXCEPT);
  return 0;
}

int feenableexcept(int __mask) {
  fenv_t __old_fcsr, __new_fcsr;
  fegetenv(&__old_fcsr);
  __new_fcsr = __old_fcsr | (__mask & FE_ALL_EXCEPT) << _ENABLE_SHIFT;
  fesetenv(&__new_fcsr);
  return ((__old_fcsr >> _ENABLE_SHIFT) & FE_ALL_EXCEPT);
}

int fedisableexcept(int __mask) {
  fenv_t __old_fcsr, __new_fcsr;
  fegetenv(&__old_fcsr);
  __new_fcsr = __old_fcsr & ~((__mask & FE_ALL_EXCEPT) << _ENABLE_SHIFT);
  fesetenv(&__new_fcsr);
  return ((__old_fcsr >> _ENABLE_SHIFT) & FE_ALL_EXCEPT);
}

int fegetexcept(void) {
  fenv_t __fcsr;
  fegetenv(&__fcsr);
  return ((__fcsr & _FCSR_ENABLE_MASK) >> _ENABLE_SHIFT);
}
