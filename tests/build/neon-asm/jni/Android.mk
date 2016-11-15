LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := foo
LOCAL_SRC_FILES := foo.S
LOCAL_CFLAGS := -mfpu=neon
include $(BUILD_STATIC_LIBRARY)
