LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := log2-test
LOCAL_SRC_FILES := log2_test.cpp
LOCAL_STATIC_LIBRARIES := googletest_main
include $(BUILD_EXECUTABLE)

$(call import-module,third_party/googletest)
