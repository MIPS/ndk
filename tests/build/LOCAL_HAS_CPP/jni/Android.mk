LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libfoo
LOCAL_SRC_FILES := foo.c
LOCAL_HAS_CPP := true
include $(BUILD_SHARED_LIBRARY)
