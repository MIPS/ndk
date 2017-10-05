LOCAL_PATH:= $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libtypes
LOCAL_SRC_FILES := types.cpp
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := libtypestest
LOCAL_SRC_FILES := types_test.cpp
LOCAL_SHARED_LIBRARIES := libtypes
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := foo
LOCAL_SRC_FILES := foo.cpp
include $(BUILD_EXECUTABLE)
