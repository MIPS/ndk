LOCAL_PATH := $(call my-dir)

# Provides foo.
include $(CLEAR_VARS)
LOCAL_MODULE := libfoo
LOCAL_SRC_FILES := foo.c
include $(BUILD_STATIC_LIBRARY)

# Provides bar.
include $(CLEAR_VARS)
LOCAL_MODULE := libbar
LOCAL_SRC_FILES := bar.c
include $(BUILD_SHARED_LIBRARY)

# Provides baz, which needs foo and bar. Since this is a static library, we need
# to link both libfoo and libbar into any of out callers.
include $(CLEAR_VARS)
LOCAL_MODULE := libbaz
LOCAL_SRC_FILES := baz.c
# NB: Normally we'd want to add these libraries to LOCAL_STATIC_LIBRARIES and
# LOCAL_SHARED_LIBRARIES to pick up any exported values from those libraries,
# but we want to make sure that these exports are used even if nothing depends
# on the module in question since there are actually two separate places this
# information needs to be recorded (this problem did come up in testing).
LOCAL_EXPORT_STATIC_LIBRARIES := libfoo
LOCAL_EXPORT_SHARED_LIBRARIES := libbar
include $(BUILD_STATIC_LIBRARY)

# Calls baz, which needs definitions of foo and bar. We get those libraries
# added to our module even though we only depend on libbaz.
include $(CLEAR_VARS)
LOCAL_MODULE := qux
LOCAL_SRC_FILES := qux.c
LOCAL_STATIC_LIBRARIES := libbaz
include $(BUILD_EXECUTABLE)
