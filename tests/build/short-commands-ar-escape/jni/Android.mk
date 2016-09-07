LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libfoo
LOCAL_SRC_FILES := foo.cpp
LOCAL_SHORT_COMMANDS := true
include $(BUILD_STATIC_LIBRARY)
