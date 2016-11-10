Unified Headers
===============

[Issue #120](https://github.com/android-ndk/ndk/issues/120)

Currently, we have a set of libc headers for each API version. In many cases
these headers are incorrect. Many expose APIs that didn't exist, and others
don't expose APIs that did.

Over the last few months we've done unified these into a single set of headers.
This single header path will be used for *every* platform level. API level
guards are handled with `#ifdef`. These headers can be found in
[prebuilts/ndk/headers].

Unified headers are built directly from the Android platform, so they will no
longer be out of date or incorrect (or at the very least, any bugs in the NDK
headers will also be a bug in the platform headers, which means we're much more
likely to find them).

[prebuilts/ndk/headers]: https://android.googlesource.com/platform/prebuilts/ndk/+/master/headers/


Known Issues
------------

 * For old (pre-L) API levels, non-x86 architectures had their `fenv.h`
   implementations inlined into the headers. This has not been preserved in the
   unified headers (this may change). If you need `fenv.h` support, you'll need
   to use `libandroid_support`. For ndk-build:

       include $(CLEAR_VARS)
       LOCAL_MODULE := foo
       LOCAL_SRC_FILES := foo.cpp
       LOCAL_STATIC_LIBRARIES := libandroid_support
       include $(BUILD_SHARED_LIBRARY)

       $(call import-module,android/support)

 * Standalone toolchains using GCC are not supported out of the box. To use GCC,
   pass `-D__ANDROID_API__=$API` when compiling.


Using Unified Headers
---------------------

Enabling unified headers will depend on your build system.

### ndk-build

Add the following to your Android.mk:

```makefile
APP_UNIFIED_HEADERS := true
```

### CMake

```bash
cmake -DANDROID_UNIFIED_HEADERS=ON ...
```

### Standalone Toolchains

```bash
$NDK/build/tools/make_standalone_toolchain.py --unified-headers ...
```

### Gradle

TBD


Supporting Unified Headers in Your Build System
-----------------------------------------------

App developers can stop reading here. The following information is only
relevant to build system engineers.

Unified headers require only a few changes compared to using the legacy NDK
headers. For reference, this patch added support to ndk-build:
https://android-review.googlesource.com/c/239934/

1. The compile time sysroot is now `$NDK/sysroot`. Previously this was
   `$NDK/platforms/android-$API/arch-$ARCH`.

2. Pass `-isystem $NDK/sysroot/usr/include/$TRIPLE` when compiling. The triple
   has the following mapping:

   Arch    | Triple
   --------|-------------------------
   ARM     | `arm-linux-androideabi`
   ARM64   | `aarch64-linux-android`
   MIPS    | `mipsel-linux-android`
   MIPS64  | `mips64el-linux-android`
   x86     | `i386-linux-android`
   x86\_64 | `x86_64-linux-android`

   This is needed for architecture specific headers such as those in `asm/` and
   `machine/`. We plan to teach Clang's driver to automatically search the
   architecture specific include directory, but that has yet to be done.

3. Pass `-D__ANDROID_API__=$API` when compiling. This define used to be provided
   by `<android/api-level.h>`, but with only one set of headers this is no
   longer possible. In the future we will look in to adding `-mandroid-version`
   or similar to Clang so this is automatic.

4. At link time, change nothing. All link time build behavior should match the
   legacy headers behavior. `--sysroot` should still point to
   `$NDK/platforms/android-$API/arch-$ARCH/`.
