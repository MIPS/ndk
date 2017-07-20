LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := vulkan
LOCAL_SRC_FILES := instance.cpp
LOCAL_CFLAGS := -std=c++11 -DVK_PROTOTYPES
LOCAL_LDLIBS := -lvulkan
LOCAL_STATIC_LIBRARIES := shaderc glslang
include $(BUILD_EXECUTABLE)

$(call import-module,third_party/shaderc)
$(call import-module,third_party/vulkan/src/build-android/jni)
