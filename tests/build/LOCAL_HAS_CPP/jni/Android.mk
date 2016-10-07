LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libfoo
LOCAL_SRC_FILES := foo.c
LOCAL_HAS_CPP := true
ifeq ($(TARGET_ARCH_ABI),armeabi)
    LOCAL_LDFLAGS := -latomic
endif
include $(BUILD_SHARED_LIBRARY)
