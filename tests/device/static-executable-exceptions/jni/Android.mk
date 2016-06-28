LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := static-executable
LOCAL_SRC_FILES := main.cpp
LOCAL_CFLAGS += -fexceptions
LOCAL_LDFLAGS += -static
include $(BUILD_EXECUTABLE)
