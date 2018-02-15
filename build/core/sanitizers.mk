#
# Copyright (C) 2018 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

NDK_TOOLCHAIN_LIB_SUFFIX := 64
ifeq ($(HOST_ARCH64),x86)
    NDK_TOOLCHAIN_LIB_SUFFIX :=
endif

NDK_TOOLCHAIN_LIB_DIR := \
    $(LLVM_TOOLCHAIN_PREBUILT_ROOT)/lib$(NDK_TOOLCHAIN_LIB_SUFFIX)/clang/5.0.2/lib/linux

NDK_APP_ASAN := $(NDK_APP_DST_DIR)/$(TARGET_ASAN_BASENAME)
NDK_APP_UBSAN := $(NDK_APP_DST_DIR)/$(TARGET_UBSAN_BASENAME)

NDK_ALL_LDFLAGS := $(NDK_APP_LDFLAGS)
$(foreach __module,$(__ndk_modules),\
    $(eval NDK_ALL_LDFLAGS += $(__ndk_modules.$(__module).LDFLAGS)))
NDK_FSANITIZE_LDFLAGS := $(filter -fsanitize=%,$(NDK_ALL_LDFLAGS))
NDK_SANITIZERS := $(patsubst -fsanitize=%,%,$(NDK_FSANITIZE_LDFLAGS))

NDK_SANITIZER_NAME := UBSAN
NDK_SANITIZER_FSANITIZE_ARGS := undefined
include $(BUILD_SYSTEM)/install_sanitizer.mk

NDK_SANITIZER_NAME := ASAN
NDK_SANITIZER_FSANITIZE_ARGS := address
include $(BUILD_SYSTEM)/install_sanitizer.mk
