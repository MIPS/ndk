LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libnativeactivity
LOCAL_SRC_FILES := android_main.cpp
LOCAL_WHOLE_STATIC_LIBRARIES := android_native_app_glue
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := oncreate_visible
LOCAL_SRC_FILES := oncreate.cpp
LOCAL_SHARED_LIBRARIES := libnativeactivity
include $(BUILD_EXECUTABLE)

include $(CLEAR_VARS)
LOCAL_MODULE := libnativeactivity_legacy
LOCAL_SRC_FILES := android_main_legacy.cpp
LOCAL_STATIC_LIBRARIES := android_native_app_glue
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := oncreate_visible_legacy
LOCAL_SRC_FILES := oncreate.cpp
LOCAL_SHARED_LIBRARIES := libnativeactivity_legacy
include $(BUILD_EXECUTABLE)

$(call import-module,android/native_app_glue)
