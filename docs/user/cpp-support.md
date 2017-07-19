# C++ Library Support

[TOC]

The NDK supports multiple C++ runtime libraries. This document provides
information about these libraries, the tradeoffs involved, and how to use them.


## Important Considerations
<a id="ic"></a>

### One STL Per App

An application should not use more than one C++ runtime. The various STLs are
**not** compatible with one another. As an example, the layout of `std::string`
in libc++ is not the same as it is in gnustl. Code written against one STL will
not be able to use objects written against another. This is just one example;
the incompatibilities are numerous.

Note: The exception to this rule is that "no STL" does not count as an STL. You
can safely use C only libraries (or even the [system] runtime, since it is not
an STL) in the same application as an STL. This rule only applies to [libc++],
[gnustl], and [stlport].

Warning: The linker can catch some of these issues at build time, but many of
these issues will only manifest as a crash or odd behavior at run time.

This rule extends beyond your code. All of your dependencies must use the same
STL that you have selected. If you depend on a closed source third-party
dependency that uses the STL and does not provide a library per STL, you do not
have a choice in STL. You must use the same STL as your dependency.

It is possible that you will depend on two mutually incompatible libraries. In
this situation the only solutions are to drop one of the dependencies or ask the
maintainer to provide a library built against the other STL.

Note: While we attempt to maintain ABI compatibility across NDK releases, this
is not always possible. For the best compatibility, you should use not only the
same STL as your dependencies but also the same version of the NDK whenever
possible.

### Static runtimes
<a id="sr"></a>

In C++, it is not safe to define more than one copy of the same function or
object in a single program. This is one aspect of the [One Definition Rule]
present in the C++ standard.

[One Definition Rule]: http://en.cppreference.com/w/cpp/language/definition

When using a static runtime (and static libraries in general), it is easy to
accidentally break this rule. For example, the following application breaks this
rule:

```makefile
# Application.mk
APP_STL := c++_static
```

```makefile
# Android.mk

include $(CLEAR_VARS)
LOCAL_MODULE := foo
LOCAL_SRC_FILES := foo.cpp
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := bar
LOCAL_SRC_FILES := bar.cpp
LOCAL_SHARED_LIBRARIES := foo
include $(BUILD_SHARED_LIBRARY)
```

In this situation, the STL, including and global data and static constructors,
will be present in both libraries. The runtime behavior of this application is
undefined, and in practice crashes are very common. Other possible issues
include:

 * Memory allocated in one library, and freed in the other, causing memory
   leakage or heap corruption.
 * Exceptions raised in `libfoo.so` going uncaught in `libbar.so`, causing your
   app to crash.
 * Buffering of `std::cout` not working properly.

Beyond the behavioral issues involved, linking the static runtime into multiple
libraries will duplicate the code in each shared library, increasing the size of
your application.

In general, you can only use a static variant of the C++ runtime if you have one
and only one shared library in your application.

Note: This rule applies to both your code and your third party dependencies.

However, if all of your application's native code is contained in a single
shared library, we recommend using the static runtime. In this situation it is
safe to do so and it will allow the linker to inline and prune as much unused
code as possible, leading to the best optimized and smallest application
possible.

### Shared runtimes

If your app targets a version of Android earlier than Android 4.3 (Android API
level 18), and you use the shared library variant of a given C++ runtime, you
must load the shared library before any other library that depends on it.

Rather than managing this yourself, we recommend using
[ReLinker](https://github.com/KeepSafe/ReLinker).


## C++ Runtime Libraries
<a id="hr"></a>

**Table 1.** NDK C++ Runtimes and Features.

| Name      | Features            |
| --------- | ------------------- |
| [libc++]  | C++1z support.      |
| [gnustl]  | C++11 support.      |
| [STLport] | C++98 support.      |
| [system]  | `new` and `delete`. |

With the exception of the system library, each of these is available as both a
static and shared library.

Warning: Using static runtimes can cause unexpected behavior. See the [static
runtimes section](#static_runtimes) for more information.

### Selecting a C++ Runtime

If you are using CMake, you can specify a runtime from Table 1 with the
`ANDROID_STL` variable in your module-level `build.gradle` file. To learn more,
see [Using CMake Variables](/ndk/guides/cmake.html#variables).

If you are using ndk-build, you can specify a runtime from Table 1 with the
`APP_STL` variable in your [Application.mk] file. For example:

```makefile
APP_STL := c++_shared
```

You may only select one runtime for your app, and can only do in
[Application.mk].

When using a [Standalone Toolchain](/ndk/guides/standalone_toolchain.html), you
select your STL with the `--stl` argument to `make_standalone_toolchain.py`. By
default your toolchain will use the shared STL. To use the static variant, add
`-static-libstdc++` to your linker flags.


## C++ Exceptions
<a id="xp"></a>

C++ exceptions are supported by most of the NDK C++ runtimes, but they are
disabled by default in ndk-build. This is because historically C++ exceptions
were not available in the NDK. CMake and standalone toolchains have C++
exceptions enabled by default.

To enable exceptions across your whole application in ndk-build, add the
following line to your [Application.mk] file:

```makefile
APP_CPPFLAGS := -fexceptions
```

To enable exceptions for a single ndk-build module, add the following line to
the given module in its [Android.mk]:

```makefile
LOCAL_CPP_FEATURES := exceptions
```

Alternatively, you can use:

```makefile
LOCAL_CPPFLAGS := -fexceptions
```


## RTTI
<a id="rt"></a>

As with exceptions, RTTI is supported by most NDK C++ runtimes, but is disabled
by default in ndk-build. CMake and standalone toolchains have RTTI enabled by
default.

To enable RTTI across your whole application in ndk-build, add the following
line to your [Application.mk] file:

```makefile
APP_CPPFLAGS := -frtti
```

To enable RTTI for a single ndk-build module, add the following line to the
given module in its [Android.mk]:

```makefile
LOCAL_CPP_FEATURES := rtti
```

Alternatively, you can use:

```makefile
LOCAL_CPPFLAGS := -frtti
```


## Runtime Characteristics
<a id="rc"></a>

### libc++:
<a id="cs"></a>

[LLVM's libc++](https://libcxx.llvm.org) is the C++ standard library that has
been used by the Android OS since Lollipop, and in the [future] will be the only
STL available in the NDK.

Until NDK r16, the NDK's libc++ is only of beta quality. Beginning with NDK r16,
libc++ will be the preferred STL. A [future] NDK release will remove the other
options.

The shared library for this runtime is `libc++_shared.so`, and the static
library is `libc++_static.a`.

libc++ is dual-licensed under both the University of Illinois "BSD-Like" license
and the MIT license. For more information, see the [license
file](https://llvm.org/svn/llvm-project/libcxx/trunk/LICENSE.TXT).

#### Compatibility

Prior to NDK r16, the NDK's libc++ is not stable. Not all the tests pass, and
the test suite is not comprehensive. There is no comprehensive list of issues,
but locales and stdio (the `sprintf` family in particular) have been known to be
unreliable.

These compatibility issues are caused by libandroid\_support, which backports
the libc APIs necessary for libc++ to old releases. These compatibility issues
have been fixed in NDK r16. This library has been rewritten and is much more
thoroughly tested.

### gnustl
<a id="gn"></a>

The [GNU C++ Library](https://gcc.gnu.org/onlinedocs/libstdc++/) is called
gnustl on Android to differentiate it from the [system](#system) runtime. This
runtime is the libstdc++ available on a GNU/Linux system.

This runtime is tightly coupled to GCC, which is no longer supported in the NDK.
As such, it has not received updates for several releases. The version in the
NDK only supports C++11, and some portions of this library are incompatible with
Clang.

Note: This library will be deprecated and removed in a [future] NDK release.
Beginning with NDK r16, you should use [libc++](#libc) instead.

The shared library for this runtime is `libgnustl_shared.so`, and the static
library is `libgnustl_static.a`.

gnustl is covered by the GPLv3 license, and *not* the LGPLv2 or LGPLv3.
For more information, see [the
license](https://gcc.gnu.org/onlinedocs/gcc-4.9.3/libstdc++/manual/manual/license.html)
on the GCC website.

### STLport
<a id="stl"></a>

This is an Android port of [STLport](http://www.stlport.org).

The upstream STLport project became inactive in 2008, and as such this runtime
does not support C++11 or newer. For modern C++ support, you should use
[libc++](#libc).

Note: This library will be deprecated and removed in a [future] NDK release.
Beginning with NDK r16, you should use [libc++](#libc) instead.

The shared library for this runtime is `libstlport_shared.so`, and the static
library is `libstlport_static.a`.

STLport is licensed under a BSD-style open-source license. See
`$NDK/sources/cxx-stl/stlport/README` for more details.

### system

The system runtime refers to `/system/lib/libstdc++.so`. This library should not
be confused with GNU's libstdc++, which is called [gnustl](#gnustl) in the NDK.

The system C++ runtime provides support for the basic C++ Runtime ABI.
Essentially, this library provides `new` and `delete`. In contrast to the other
options available in the NDK, there is no support for exception handling or
RTTI.

There is no standard library support aside from the C++ wrappers for the C
library headers such as `<cstdio>`. If you want an STL, you should use one of
the other options presented on this page.

Note: This is the only C++ Runtime that is provided by the OS. All other
runtimes must be included in your APK.

[Android.mk]: /ndk/guides/android_mk.html
[Application.mk]: /ndk/guides/application_mk.html
[libc++]: #libc
[gnustl]: #gnustl
[stlport]: #stlport
[system]: #system
[future]: https://android.googlesource.com/platform/ndk/+/master/docs/Roadmap.md
