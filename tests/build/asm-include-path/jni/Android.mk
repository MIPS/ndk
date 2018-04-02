LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := asm-include-path
LOCAL_SRC_FILES := foo.S
include $(BUILD_SHARED_LIBRARY)
