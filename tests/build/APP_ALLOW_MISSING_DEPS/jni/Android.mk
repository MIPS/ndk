LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := foo
LOCAL_SRC_FILES := foo.cpp
LOCAL_STATIC_LIBRARIES := missing-dep
include $(BUILD_EXECUTABLE)
