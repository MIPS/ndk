LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := stack_crash
LOCAL_SRC_FILES := stack_crash.cpp
LOCAL_CFLAGS := -O2
ifeq ($(TARGET_ARCH_ABI),armeabi)
    LOCAL_LDFLAGS := -latomic
endif
include $(BUILD_EXECUTABLE)
