LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := vulkan
LOCAL_SRC_FILES := instance.cpp
LOCAL_CFLAGS := -std=c++11 -DVK_PROTOTYPES
LOCAL_LDLIBS := -lvulkan
include $(BUILD_EXECUTABLE)
