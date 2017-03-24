LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := foo
LOCAL_SRC_FILES := foo.c
LOCAL_CFLAGS := -Wno-error=return-type
include $(BUILD_STATIC_LIBRARY)
