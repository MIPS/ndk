LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := gets-gnustl
LOCAL_SRC_FILES := gets-gnustl.cpp
LOCAL_CFLAGS += -Wall -Werror -std=c++14
include $(BUILD_EXECUTABLE)
