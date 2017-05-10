LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := gets-stlport
LOCAL_SRC_FILES := gets-stlport.cpp
LOCAL_CFLAGS += -Wall -Werror -std=c++14
include $(BUILD_EXECUTABLE)
