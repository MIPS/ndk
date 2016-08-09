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

Known Issues
------------

 * This is not intended to be a comprehensive list of all outstanding bugs.
 * Standlone toolchains using libc++ and GCC do not work. This seems to be a bug
   in GCC. See the following commit message for more details:
   https://android-review.googlesource.com/#/c/247498
 * x86 ASAN still doesn't work. See discussion on
   https://android-review.googlesource.com/#/c/186276/
 * Exception unwinding with `c++_shared` still does not work for ARM on
   Gingerbread or Ice Cream Sandwich.
 * Bionic headers and libraries for Marshmallow and N are not yet exposed
   despite the presence of android-24. Those platforms are still the Lollipop
   headers and libraries (not a regression from r11).
 * RenderScript tools are not present (not a regression from r11):
   https://github.com/android-ndk/ndk/issues/7.
