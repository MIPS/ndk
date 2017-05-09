LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libnativeactivity
LOCAL_SRC_FILES := android_main.cpp
LOCAL_WHOLE_STATIC_LIBRARIES := android_native_app_glue
include $(BUILD_SHARED_LIBRARY)

$(call import-module,android/native_app_glue)
