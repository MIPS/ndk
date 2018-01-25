LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := static-executable
LOCAL_SRC_FILES := main.cpp
LOCAL_CPPFLAGS := -fexceptions
LOCAL_LDFLAGS := -static -Wl,--eh-frame-hdr
include $(BUILD_EXECUTABLE)
