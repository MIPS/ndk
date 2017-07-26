LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := gets-libcxx
LOCAL_SRC_FILES := gets-libcxx.cpp
LOCAL_CPPFLAGS := -std=c++14
ifneq ($(NDK_TOOLCHAIN_VERSION),4.9)
    # GCC has -Wattribute errors with libc++'s math.h because it conflicts with
    # GCC's builtin definition of abs (math.h defines noexcept floating point
    # overrides).
    LOCAL_CFLAGS += -Wall -Werror
endif
include $(BUILD_EXECUTABLE)
