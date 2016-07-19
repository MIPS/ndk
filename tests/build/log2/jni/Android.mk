LOCAL_PATH := $(call my-dir)

# The intention of this test is to ensure that we get the include ordering right
# for libc++ -> libandroid_support -> libc, and to make sure we're actually
# linking libandroid_support with libc++_shared.
# http://b.android.com/212634
include $(CLEAR_VARS)
LOCAL_MODULE := log2_test
LOCAL_SRC_FILES := log2_test.cpp
include $(BUILD_EXECUTABLE)
