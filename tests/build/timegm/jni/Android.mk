LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libtimetest
LOCAL_SRC_FILES := timetest.cpp
include $(BUILD_SHARED_LIBRARY)
