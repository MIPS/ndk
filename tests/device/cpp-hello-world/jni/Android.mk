LOCAL_PATH := $(call my-dir)

ifeq (none,$(APP_STL))
DEFINES := -DNONE
else ifeq (system,$(APP_STL))
DEFINES += -DSYSTEM
endif

include $(CLEAR_VARS)
LOCAL_MODULE := hello-world
LOCAL_SRC_FILES := hello-world.cpp
LOCAL_CPPFLAGS := $(DEFINES)
include $(BUILD_EXECUTABLE)
