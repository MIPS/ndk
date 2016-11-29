LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := libbar
LOCAL_SRC_FILES := bar.c
LOCAL_CFLAGS := -flto
include $(BUILD_STATIC_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := flto
LOCAL_SRC_FILES := flto.c
LOCAL_STATIC_LIBRARIES := libbar
LOCAL_CFLAGS += -flto
LOCAL_LDFLAGS += -flto

# Clang LTO is only supported with gold. ARM64 still uses bfd by default, so
# make sure this test uses gold when we're using clang.
ifneq ($(filter clang%,$(NDK_TOOLCHAIN_VERSION)),)
LOCAL_CFLAGS += -fuse-ld=gold
LOCAL_LDFLAGS += -fuse-ld=gold
endif

include $(BUILD_EXECUTABLE)
