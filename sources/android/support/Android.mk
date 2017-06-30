LOCAL_PATH := $(call my-dir)

android_support_export_c_includes := $(LOCAL_PATH)/include

ifneq ($(filter $(NDK_KNOWN_DEVICE_ABI64S),$(TARGET_ARCH_ABI)),)
    is_lp64 := true
else
    is_lp64 :=
endif

ifneq ($(LIBCXX_FORCE_REBUILD),true) # Using prebuilt

LIBCXX_LIBS := ../../cxx-stl/llvm-libc++/libs/$(TARGET_ARCH_ABI)

include $(CLEAR_VARS)
LOCAL_MODULE := android_support
LOCAL_SRC_FILES := $(LIBCXX_LIBS)/lib$(LOCAL_MODULE)$(TARGET_LIB_EXTENSION)
LOCAL_EXPORT_C_INCLUDES := $(android_support_export_c_includes)
include $(PREBUILT_STATIC_LIBRARY)

else # Building

android_support_c_includes := $(android_support_export_c_includes)

ifeq ($(is_lp64),true)
# 64-bit ABIs

# We don't need this file on LP32 because libc++ has its own fallbacks for these
# functions. We can't use those fallbacks for LP64 because the file contains all
# the strto*_l functions. LP64 had some of those in L, so the inlines in libc++
# collide with the out-of-line declarations in bionic.
android_support_sources := \
    src/locale_support.cpp \

else
# 32-bit ABIs

BIONIC_PATH := ../../../../bionic

android_support_c_includes += $(BIONIC_PATH)/libc

android_support_sources := \
    $(BIONIC_PATH)/libc/bionic/c32rtomb.cpp \
    $(BIONIC_PATH)/libc/bionic/mbrtoc32.cpp \
    $(BIONIC_PATH)/libc/bionic/mbstate.cpp \
    $(BIONIC_PATH)/libc/bionic/wchar.cpp \
    $(BIONIC_PATH)/libc/upstream-openbsd/lib/libc/locale/mbtowc.c \
    src/_Exit.cpp \
    src/iswblank.cpp \
    src/posix_memalign.cpp \
    src/swprintf.cpp \

# These are old sources that should be purged/rewritten/taken from bionic.
android_support_sources += \
    src/locale/duplocale.c \
    src/locale/freelocale.c \
    src/locale/localeconv.c \
    src/locale/newlocale.c \
    src/locale/uselocale.c \
    src/math_support.c \
    src/msun/e_log2.c \
    src/msun/e_log2f.c \
    src/msun/s_nan.c \
    src/musl-math/frexp.c \
    src/musl-math/frexpf.c \
    src/musl-math/frexpl.c \
    src/stdlib_support.c \
    src/wchar_support.c \
    src/wcstox/floatscan.c \
    src/wcstox/intscan.c \
    src/wcstox/shgetc.c \
    src/wcstox/wcstod.c \
    src/wcstox/wcstol.c \

# Replaces broken implementations in x86 libm.so
ifeq (x86,$(TARGET_ARCH_ABI))
android_support_sources += \
    src/musl-math/scalbln.c \
    src/musl-math/scalblnf.c \
    src/musl-math/scalblnl.c \
    src/musl-math/scalbnl.c \

endif

endif  # 64-/32-bit ABIs

# This is only available as a static library for now.
include $(CLEAR_VARS)
LOCAL_MODULE := android_support
LOCAL_SRC_FILES := $(android_support_sources)
LOCAL_C_INCLUDES := $(android_support_c_includes)
LOCAL_CFLAGS := \
    -Drestrict=__restrict__ \
    -ffunction-sections \
    -fdata-sections \
    -fvisibility=hidden \

LOCAL_CPPFLAGS := \
    -fvisibility-inlines-hidden \
    -std=c++11 \

# These Clang warnings are triggered by the Musl sources. The code is fine,
# but we don't want to modify it. TODO(digit): This is potentially dangerous,
# see if there is a way to build the Musl sources in a separate static library
# and have the main one depend on it, or include its object files.
ifneq ($(TARGET_TOOLCHAIN),$(subst clang,,$(TARGET_TOOLCHAIN)))
LOCAL_CFLAGS += \
  -Wno-shift-op-parentheses \
  -Wno-string-plus-int \
  -Wno-dangling-else \
  -Wno-bitwise-op-parentheses \
  -Wno-shift-negative-value
endif

LOCAL_EXPORT_C_INCLUDES := $(android_support_export_c_includes)

include $(BUILD_STATIC_LIBRARY)

endif # Prebuilt/building
