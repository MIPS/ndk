LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := asflags
LOCAL_SRC_FILES := foo.S bar.c
ifneq (,$(filter x86 x86_64,$(TARGET_ARCH)))
    # .asm is specifically yasm, and only supported for x86/x86_64.
    LOCAL_SRC_FILES += baz.asm
endif
LOCAL_ASFLAGS := -DLOCAL_ASFLAG
LOCAL_CFLAGS := -DLOCAL_CFLAG
LOCAL_CONLYFLAGS := -DLOCAL_CONLYFLAG
LOCAL_ASMFLAGS := -DLOCAL_ASMFLAG
include $(BUILD_SHARED_LIBRARY)
