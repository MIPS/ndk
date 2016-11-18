LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := foo
LOCAL_SRC_FILES := foo.cpp
ifeq ($(TARGET_ARCH_ABI),armeabi)
    LOCAL_LDLIBS := -latomic
endif
include $(BUILD_EXECUTABLE)
