LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := gets-libcxx
LOCAL_SRC_FILES := gets-libcxx.cpp
LOCAL_CFLAGS += -Wall -Werror -std=c++14
include $(BUILD_EXECUTABLE)
