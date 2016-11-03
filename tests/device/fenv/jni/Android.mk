LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := test_fenv_c
LOCAL_SRC_FILES := test_fenv.c
LOCAL_STATIC_LIBRARIES := libandroid_support
include $(BUILD_EXECUTABLE)

$(call import-module,android/support)
