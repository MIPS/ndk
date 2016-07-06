LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := pch
LOCAL_PCH := stdafx.h
LOCAL_SRC_FILES := untagged.cpp maybe_tagged.cpp
LOCAL_CFLAGS := -Werror
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := pch-arm
LOCAL_PCH := stdafx.h
LOCAL_SRC_FILES := untagged.cpp maybe_tagged.cpp.arm
LOCAL_CFLAGS := -Werror
include $(BUILD_SHARED_LIBRARY)

# armeabi doesn't support neon, but we want to build the rest of the test for
# that ABI.
ifneq ($(TARGET_ARCH_ABI),armeabi)
include $(CLEAR_VARS)
LOCAL_MODULE := pch-neon
LOCAL_PCH := stdafx.h
LOCAL_SRC_FILES := untagged.cpp maybe_tagged.cpp.neon
LOCAL_CFLAGS := -Werror
include $(BUILD_SHARED_LIBRARY)
endif

# We also need to check that we get the PCH tags right for the defaults.
# See https://github.com/android-ndk/ndk/issues/149.

include $(CLEAR_VARS)
LOCAL_MODULE := pch-local-arm-mode
LOCAL_PCH := stdafx.h
LOCAL_SRC_FILES := untagged.cpp
LOCAL_CFLAGS := -Werror
LOCAL_ARM_MODE := arm
include $(BUILD_SHARED_LIBRARY)

# Another neon test. Can't be built for armeabi.
ifneq ($(TARGET_ARCH_ABI),armeabi)
include $(CLEAR_VARS)
LOCAL_MODULE := pch-local-arm-neon
LOCAL_PCH := stdafx.h
LOCAL_SRC_FILES := untagged.cpp
LOCAL_CFLAGS := -Werror
LOCAL_ARM_NEON := true
include $(BUILD_SHARED_LIBRARY)
endif
