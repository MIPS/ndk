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

 * The Play Store will require 64-bit support when uploading an APK beginning in
   August 2019. Start porting now to avoid surprises when the time comes. For
   more information, see [this blog post](https://android-developers.googleblog.com/2017/12/improving-app-security-and-performance.html).

NDK
---

 * Updated Clang to build 4393122 based on ???
 * AArch64 now uses gold by default, matching the other architectures.
 * Updated gtest to upstream revision 0fe96607d85cf3a25ac40da369db62bbee2939a5.
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

Known Issues
------------

 * This is not intended to be a comprehensive list of all outstanding bugs.
 * [Issue 360]: `thread_local` variables with non-trivial destructors will cause
   segfaults if the containing library is `dlclose`ed on devices running M or
   newer, or devices before M when using a static STL. The simple workaround is
   to not call `dlclose`.

[Issue 360]: https://github.com/android-ndk/ndk/issues/360
