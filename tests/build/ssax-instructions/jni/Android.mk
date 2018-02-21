LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := ssax_instruction
LOCAL_ARM_NEON := true
LOCAL_SRC_FILES := test.S
ifneq ($(filter clang%,$(NDK_TOOLCHAIN_VERSION)),)
    # asm is not compatible with Clang's assembler.
    LOCAL_ASFLAGS := -fno-integrated-as
endif
include $(BUILD_SHARED_LIBRARY)
