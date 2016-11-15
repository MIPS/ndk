Common Problems and Solutions
=============================

This document lists common issues that users encounter when using the NDK. It is
by no means complete, but represents some of the most common non-bugs we see
filed.


Target API Set Higher Than Device API
-------------------------------------

The target API level in the NDK has a very different meaning than it does in
Java. The NDK target API level is your app's **minimum** supported API level. In
ndk-build, this is your `APP_PLATFORM` setting.

Since references to functions are (typically) resolved when a library is
loaded rather than when they are first called, you cannot reference APIs that
are not always present and guard their use with API level checks. If they are
referred to at all, they must be present.

**Problem**: Your target API level is higher than the API supported by your
device.

**Solution**: Set your target API level (`APP_PLATFORM`) to the minimum version
of Android your app supports.

Build System         | Setting
---------------------|-------------------
ndk-build            | `APP_PLATFORM`
CMake                | `ANDROID_PLATFORM`
Standalone Toolchain | `--api`
Gradle               | TODO: No idea

### Cannot Locate `__aeabi` Symbols

> UnsatisfiedLinkError: dlopen failed: cannot locate symbol "`__aeabi_memcpy`"

Note that these are *runtime* errors. These errors will appear in the log when
you attempt to load your native libraries. The symbol might be any of
`__aeabi_*` (`__aeabi_memcpy` and `__aeabi_memclr` seem to be the most common).

This problem is documented at https://github.com/android-ndk/ndk/issues/126.

### Cannot Locate Symbol `rand`

> UnsatisfiedLinkError: dlopen failed: cannot locate symbol "`rand`"

This problem was explained very well on Stack Overflow:
http://stackoverflow.com/a/27338365/632035

There are a handful of other symbols that are also affected by this.
TODO: Figure out what the other ones were.


Undefined Reference to `__atomic_*`
-----------------------------------

**Problem**: Some ABIs (particularly armeabi) need libatomic to provide some
implementations for atomic operations.

**Solution**: Add `-latomic` when linking.

> error: undefined reference to '`__atomic_exchange_4`'

The actual symbol here might be anything prefixed with `__atomic_`.


Using Mismatched Prebuilt Libraries
-----------------------------------

Using prebuilt libraries (third-party libraries, typically) in your application
requires a bit of extra care. In general, the following rules need to be
followed:

* Your minimum API level is the maximum of all API levels targeted by all
  libraries.

  If your target API level is android-9, but you're using a prebuilt library
  that was built against android-16, your minimum API level is android-16.
  Failure to adhere to this will be visible at build time if the prebuilt
  library is static, but may not appear until run time for prebuilt shared
  libraries.

* All libraries should be generated with the same NDK version.

  This rule is a bit more flexible than most, but in general NDK code is only
  guaranteed to be compatible with code generated with the same version of the
  NDK (minor revision mismatches generally okay).

* All libraries must use the same STL.

  A library using libc++ will not interoperate with one using stlport. All
  libraries in an application must use the same STL.

  Strictly speaking this can be made to work, but it's a very fragile
  configuration. Avoid it.

* Apps with multiple shared libraries must use a shared STL.

  https://developer.android.com/ndk/guides/cpp-support.html#sr

  As with mismatches STLs, the problems caused by this can be avoided if great
  care is taken, but it's better to just avoid the problem.
