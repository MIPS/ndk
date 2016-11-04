Changelog
=========

Report issues to [GitHub].

For Android Studio issues, follow the docs on the [Android Studio site].

[GitHub]: https://github.com/android-ndk/ndk/issues
[Android Studio site]: http://tools.android.com/filing-bugs

Announcements
-------------

* GCC is no longer supported. It will not be removed from the NDK just yet, but
  is no longer receiving backports. It cannot be removed until after libc++ has
  become stable enough to be the default, as some parts of gnustl are still
  incompatible with Clang. It will likely be removed after that point.

ndk-build
---------

 * Module builds will now fail if they have any missing dependencies. To revert
   to the old behavior, set `APP_ALLOW_MISSING_DEPS=false`. See
   https://github.com/android-ndk/ndk/issues/208.

Clang/LLVM
----------

 * The x86 ASAN issues noted since r11 appear to have been emulator specific.
   Up to date emulators no longer have this issue.

Known Issues
------------

 * This is not intended to be a comprehensive list of all outstanding bugs.
 * Standlone toolchains using libc++ and GCC do not work. This seems to be a bug
   in GCC. See the following commit message for more details:
   https://android-review.googlesource.com/#/c/247498
 * Standalone toolchains using GCC do not work out of the box with unified
   headers. They can be made to work by passing `-D__ANDROID_API__=21`
   (replacing 21 with the same API level you passed to
   `make_standalone_toolchain.py`) when compiling.
 * Bionic headers and libraries for Marshmallow and N are not yet exposed
   despite the presence of android-24. Those platforms are still the Lollipop
   headers and libraries (not a regression from r11).
 * RenderScript tools are not present (not a regression from r11):
   https://github.com/android-ndk/ndk/issues/7.
