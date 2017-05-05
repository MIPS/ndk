LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := unified_SIGRTMIN
LOCAL_SRC_FILES := unified_SIGRTMIN.cpp
include $(BUILD_EXECUTABLE)

include $(CLEAR_VARS)
LOCAL_MODULE := unified_SIGRTMAX
LOCAL_SRC_FILES := unified_SIGRTMAX.c
include $(BUILD_EXECUTABLE)
