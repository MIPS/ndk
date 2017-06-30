LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := ffs
LOCAL_SRC_FILES := ffs.c
include $(BUILD_EXECUTABLE)
