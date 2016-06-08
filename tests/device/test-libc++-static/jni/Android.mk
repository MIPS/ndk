LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := test_1_static
LOCAL_SRC_FILES := test_1.cc
ifeq ($(TARGET_ARCH_ABI),armeabi)
    # Only need -latomic for armeabi.
    LOCAL_LDLIBS := -latomic
endif
include $(BUILD_EXECUTABLE)
