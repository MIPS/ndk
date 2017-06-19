LOCAL_PATH := $(call my-dir)

# Module declaration for the unit test program.
include $(CLEAR_VARS)
LOCAL_MODULE := android_support_unittests
LOCAL_SRC_FILES := \
  ctype_test.cpp \
  math_test.cpp \
  stdio_test.cpp \
  wchar_test.cpp \

LOCAL_STATIC_LIBRARIES := android_support googletest_static googletest_main
include $(BUILD_EXECUTABLE)

$(call import-module,android/support)
$(call import-module,third_party/googletest)
