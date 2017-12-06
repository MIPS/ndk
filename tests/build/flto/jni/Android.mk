LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libbar
LOCAL_SRC_FILES := bar.c
LOCAL_CFLAGS := -flto
include $(BUILD_STATIC_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := flto
LOCAL_SRC_FILES := flto.c
LOCAL_STATIC_LIBRARIES := libbar
LOCAL_CFLAGS += -flto
LOCAL_LDFLAGS += -flto

include $(BUILD_EXECUTABLE)
