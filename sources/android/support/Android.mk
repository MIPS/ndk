LOCAL_PATH := $(call my-dir)

android_support_c_includes := $(LOCAL_PATH)/include

ifneq ($(filter $(NDK_KNOWN_DEVICE_ABI64S),$(TARGET_ARCH_ABI)),)
    is_lp64 := true
else
    is_lp64 :=
endif

ifeq ($(is_lp64),true)
# 64-bit ABIs
android_support_sources := \
    src/locale_support.c \

else
# 32-bit ABIs

android_support_sources := \
    src/_Exit.cpp \
    src/locale/duplocale.c \
    src/locale/freelocale.c \
    src/locale/localeconv.c \
    src/locale/newlocale.c \
    src/locale/uselocale.c \
    src/locale_support.c \
    src/math_support.c \
    src/msun/e_log2.c \
    src/msun/e_log2f.c \
    src/msun/s_nan.c \
    src/musl-ctype/iswalnum.c \
    src/musl-ctype/iswalpha.c \
    src/musl-ctype/iswblank.c \
    src/musl-ctype/iswcntrl.c \
    src/musl-ctype/iswctype.c \
    src/musl-ctype/iswdigit.c \
    src/musl-ctype/iswgraph.c \
    src/musl-ctype/iswlower.c \
    src/musl-ctype/iswprint.c \
    src/musl-ctype/iswpunct.c \
    src/musl-ctype/iswspace.c \
    src/musl-ctype/iswupper.c \
    src/musl-ctype/iswxdigit.c \
    src/musl-ctype/towctrans.c \
    src/musl-ctype/wcswidth.c \
    src/musl-ctype/wctrans.c \
    src/musl-ctype/wcwidth.c \
    src/musl-math/frexp.c \
    src/musl-math/frexpf.c \
    src/musl-math/frexpl.c \
    src/posix_memalign.cpp \
    src/stdlib_support.c \
    src/swprintf.cpp \
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

ifneq ($(LIBCXX_FORCE_REBUILD),true) # Using prebuilt

LIBCXX_LIBS := ../../cxx-stl/llvm-libc++/libs/$(TARGET_ARCH_ABI)

include $(CLEAR_VARS)
LOCAL_MODULE := android_support
LOCAL_SRC_FILES := $(LIBCXX_LIBS)/lib$(LOCAL_MODULE)$(TARGET_LIB_EXTENSION)
LOCAL_EXPORT_C_INCLUDES := $(android_support_c_includes)
include $(PREBUILT_STATIC_LIBRARY)

else # Building

BIONIC_PATH := ../../../../bionic

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

LOCAL_EXPORT_C_INCLUDES := $(android_support_c_includes)

ifneq ($(is_lp64),true)
LOCAL_SRC_FILES += \
    $(BIONIC_PATH)/libc/bionic/c32rtomb.cpp \
    $(BIONIC_PATH)/libc/bionic/mbstate.cpp \
    $(BIONIC_PATH)/libc/bionic/mbrtoc32.cpp \
    $(BIONIC_PATH)/libc/bionic/wchar.cpp \
    $(BIONIC_PATH)/libc/upstream-openbsd/lib/libc/locale/mbtowc.c \

LOCAL_C_INCLUDES += $(BIONIC_PATH)/libc
endif

include $(BUILD_STATIC_LIBRARY)

endif # Prebuilt/building
