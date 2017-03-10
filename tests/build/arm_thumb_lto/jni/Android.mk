LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := foo
LOCAL_SRC_FILES := foo.cpp bar.cpp.arm
LOCAL_CFLAGS := -flto
LOCAL_LDFLAGS := -flto
include $(BUILD_SHARED_LIBRARY)
