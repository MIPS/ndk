LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := hello-world
LOCAL_SRC_FILES := hello-world.c
include $(BUILD_EXECUTABLE)
