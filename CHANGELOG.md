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
   [this blog post].

 * gnustl and stlport are deprecated and will be removed in NDK r18.

 * Support for ARMv5 (armeabi), MIPS, and MIPS64 has been removed. Attempting to
   build any of these ABIs will result in an error.

[this blog post]: https://android-developers.googleblog.com/2017/09/introducing-android-native-development.html

NDK
---

 * Updated Clang to build 4393122 based on ???

Known Issues
------------

 * This is not intended to be a comprehensive list of all outstanding bugs.
 * [Issue 360]: `thread_local` variables with non-trivial destructors will cause
   segfaults if the containing library is `dlclose`ed on devices running M or
   newer, or devices before M when using a static STL. The simple workaround is
   to not call `dlclose`.

[Issue 360]: https://github.com/android-ndk/ndk/issues/360
