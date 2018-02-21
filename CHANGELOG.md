Changelog
=========

Report issues to [GitHub].

For Android Studio issues, follow the docs on the [Android Studio site].

[GitHub]: https://github.com/android-ndk/ndk/issues
[Android Studio site]: http://tools.android.com/filing-bugs

Announcements
-------------

 * GCC is no longer supported. It will be removed in NDK r18.

 * `libc++` is now the default STL for CMake and standalone toolchains. If you
   manually selected a different STL, we strongly encourage you to move to
   `libc++`. Note that ndk-build still defaults to no STL. For more details, see
   [this blog post](https://android-developers.googleblog.com/2017/09/introducing-android-native-development.html).

 * gnustl and stlport are deprecated and will be removed in NDK r18.

 * Support for ARMv5 (armeabi), MIPS, and MIPS64 has been removed. Attempting to
   build any of these ABIs will result in an error.

 * Support for ICS (android-14 and android-15) will be removed from r18.

 * The Play Store will require 64-bit support when uploading an APK beginning in
   August 2019. Start porting now to avoid surprises when the time comes. For
   more information, see [this blog post](https://android-developers.googleblog.com/2017/12/improving-app-security-and-performance.html).

NDK
---

 * Updated Clang to build 4479392.
     * LTO now works on Windows, fixing [Issue 313].
 * Updated gtest to upstream revision 0fe96607d85cf3a25ac40da369db62bbee2939a5.
 * `libandroid_support` is no longer used when your NDK API level is greater
   than or equal to 21 (Lollipop). Build system maintainers: be sure to update
   your build systems to account for this.
 * The platform static libraries (libc.a, libm.a, etc.) have been updated.
     * All NDK platforms now contain a modern version of these static libraries.
       Previously they were all Gingerbread (perhaps even older) or Lollipop.
     * Prior NDKs could not use the static libraries with a modern NDK API level
       because of symbol collisions between libc.a and libandroid_support. This
       has been solved by removing libandroid_support for modern API levels. A
       side effect of this is that you must now target at least android-21 to
       use the static libraries, but these binaries will still work on older
       devices.
 * Fixed parsing of the NDK revision in CMake. NDK version information is now
   available in the following CMake variables:
     * `ANDROID_NDK_REVISION`: The full string in the source.properties file.
     * `ANDROID_NDK_MAJOR`: The major revision of the NDK. For example: the 16
       in r16b.
     * `ANDROID_NDK_MINOR`: The minor revision of the NDK. For example: the b
       (represented as 1) in r16b.
     * `ANDROID_NDK_BUILD`: The build number of the NDK. This is 0 in the case
       of a local development build.
     * `ANDROID_NDK_BETA`: The beta version of the NDK. This is 0 for a stable
       release.
 * Added support for `APP_WRAP_SH` to ndk-build.
     * This variable points to a shell script (relative to your Android.mk) that
       will be installed as a [wrap.sh] file in your APK.
     * Available in both an ABI-generic form (`APP_WRAP_SH`), which will install
       a single script for every ABI, and an ABI-specific form
       (`APP_WRAP_SH_arm64-v8a`, etc) to allow for per-ABI customization of the
       wrap.sh script.
 * ndk-build now installs sanitizer runtime libraries to your out directory for
   inclusion in your APK. Coupled with [wrap.sh], this removes the requirement
   of rooting your device to use sanitizers. See [Issue 540].
 * When using ASAN, ndk-build will install a wrap.sh file to set up ASAN for
   your app if you have not specified your own wrap.sh. If you have specified
   your own wrap.sh, you can add ASAN support to it as described
   [here](https://github.com/google/sanitizers/wiki/AddressSanitizerOnAndroidO).

[wrap.sh]: https://developer.android.com/ndk/guides/wrap-script.html
[Issue 540]: https://github.com/android-ndk/ndk/issues/540

[Issue 313]: https://github.com/android-ndk/ndk/issues/313

Known Issues
------------

 * This is not intended to be a comprehensive list of all outstanding bugs.
 * [Issue 360]: `thread_local` variables with non-trivial destructors will cause
   segfaults if the containing library is `dlclose`ed on devices running M or
   newer, or devices before M when using a static STL. The simple workaround is
   to not call `dlclose`.
 * [Issue 593]: Exception handling does not work out-of-the-box with non-arm32
   static executables. Clang does not pass `--eh-frame-hdr` to the linker for
   static executables. This will be fixed in a future Clang update, but for now
   this issue can be worked around by adding `-Wl,--eh-frame-hdr` to your
   ldflags.
 * [Issue 70838247]: Gold emits broken debug information for AArch64. AArch64
   still uses BFD by default.

[Issue 360]: https://github.com/android-ndk/ndk/issues/360
[Issue 593]: https://github.com/android-ndk/ndk/issues/593
[Issue 70838247]: https://issuetracker.google.com/70838247
