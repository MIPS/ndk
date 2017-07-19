# C++ Library Support

[TOC]

The Android platform provides a very minimal C++ runtime support library, called
`system`, which is the default runtime when using ndk-build. This minimal
support does not include, for example:

 * Standard C++ Library support (except a few trivial headers).
 * C++ exceptions support
 * RTTI support

The NDK provides headers for use with this default library. In addition, the NDK
provides a number of helper runtimes that provide additional features. This page
provides information about these helper runtimes, their characteristics, and how
to use them.

Warning: Using static runtimes can cause unexpected behavior. See the [static
runtimes section](#static_runtimes) for more information.


## Helper Runtimes
<a id="hr"></a>

Table 1 provides names, brief explanations, and features of runtimes available
in the NDK.

**Table 1.** NDK Runtimes and Features.

<table>
  <colgroup>
    <col width="25%">
  </colgroup>
  <tr>
    <th>Name</th>
    <th>Explanation</th>
    <th>Features</th>
  </tr>

  <!-- System "STL" -->
  <tr>
    <td><a href="#system"><code>system</code></a></td>
    <td>
      The minimal system C++ runtime library and the default runtime when using
      ndk-build or the
      <a href="http://tools.android.com/tech-docs/new-build-system/gradle-experimental">
        experimental Gradle plugin</a>.
      <p class="note">
        <strong>Note:</strong> The shared object library for this runtime,
        <code>libstdc++.so</code>, is an Android-specific implementation of a
        minimal C++ runtime. It is not the same as the GNU libstdc++ runtime
        library.
      </p>
    </td>
    <td>N/A</td>
  </tr>

  <!-- gabi++_static -->
  <tr>
    <td><a href="#ga"><code>gabi++_static</code></a></td>
    <td>The GAbi++ runtime (static library).</td>
    <td>C++ Exceptions and RTTI</td>
  </tr>

  <!-- gabi++_shared -->
  <tr>
    <td><a href="#ga"><code>gabi++_shared</code></a></td>
    <td>The GAbi++ runtime (shared library).</td>
    <td>C++ Exceptions and RTTI</td>
  </tr>

  <!-- stlport_static -->
  <tr>
    <td><a href="#stl"><code>stlport_static</code></a></td>
    <td>The STLport runtime (static library).</td>
    <td>C++ Exceptions and RTTI; Standard Library</td>
  </tr>

  <!-- stlport_shared -->
  <tr>
    <td><a href="#stl"><code>stlport_shared</code></a></td>
    <td>The STLport runtime (shared library).</td>
    <td>C++ Exceptions and RTTI; Standard Library</td>
  </tr>

  <!-- gnustl_static -->
  <tr>
    <td><a href="#gn"><code>gnustl_static</code></a></td>
    <td>
      The GNU STL (static library). This is the default runtime when using CMake
      or a standalone toolchain.
    </td>
    <td>C++ Exceptions and RTTI; Standard Library</td>
  </tr>

  <!-- gnustl_shared -->
  <tr>
    <td><a href="#gn"><code>gnustl_shared</code></a></td>
    <td>The GNU STL (shared library).</td>
    <td>C++ Exceptions and RTTI; Standard Library</td>
  </tr>

  <!-- c++_static -->
  <tr>
    <td><a href="#cs"><code>c++_static</code></a></td>
    <td>The LLVM libc++ runtime (static library).</td>
    <td>C++ Exceptions and RTTI; Standard Library</td>
  </tr>

  <!-- c++_shared -->
  <tr>
    <td><a href="#cs"><code>c++_shared</code></a></td>
    <td>The LLVM libc++ runtime (shared library).</td>
    <td>C++ Exceptions and RTTI; Standard Library</td>
  </tr>
</table>


### How to set your runtime

If you are using CMake, you can specify a runtime from table 1 with the
`ANDROID_STL` variable in your module-level `build.gradle` file. To learn more,
go to [Using CMake Variables](/ndk/guides/cmake.html#variables).

If you are using ndk-build, you can specify a runtime from table 1 with the
`APP_STL` variable in your [Application.mk] file. For example:

```makefile
APP_STL := gnustl_static
```

You may only select one runtime for your app, and can only do in
[Application.mk].

Even if you do not use the NDK build system, you can still use STLport, libc++
or GNU STL. For more information on how to use these runtimes with your own
toolchain, see [Standalone Toolchain](/ndk/guides/standalone_toolchain.html).


## Runtime Characteristics
<a id="rc"></a>

### system

This runtime only provides the following headers, with no support beyond them:

 * `cassert`
 * `cctype`
 * `cerrno`
 * `cfloat`
 * `climits`
 * `cmath`
 * `csetjmp`
 * `csignal`
 * `cstddef`
 * `cstdint`
 * `cstdio`
 * `cstdlib`
 * `cstring`
 * `ctime`
 * `cwchar`
 * `new`
 * `stl_pair.h`
 * `typeinfo`
 * `utility`

### GAbi++ runtime
<a id="ga"></a>

This runtime provides the same headers as the default runtime, but adds support
for RTTI (RunTime Type Information) and exception handling.


### STLport runtime
<a id="stl"></a>

This runtime is an Android port of STLport (<http://www.stlport.org>). It
provides a complete set of C++ standard library headers. It also, by embedding
its own instance of GAbi++, provides support for RTTI and exception handling.

While shared and static versions of this runtime are avilable, we recommend
using the shared version. For more information, see [Static
runtimes](#static_runtimes).

The shared library file is named `libstlport_shared.so` instead of
`libstdc++.so` as is common on other platforms.

In addition to the static- and shared-library options, you can also force the
NDK to build the library from sources by adding the following line to your
`Application.mk` file, or setting it in your environment prior to building:

```makefile
STLPORT_FORCE_REBUILD := true
```

### GNU STL runtime
<a id="gn"></a>

This runtime is the GNU Standard C++ Library, (`libstdc++-v3`). Its shared
library file is named `libgnustl_shared.so`.


### libc++ runtime:
<a id="cs"></a>

This runtime is an Android port of [LLVM libc++](https://libcxx.llvm.org). Its
shared library file is named `libc++_shared.so`.

By default, this runtime compiles with `-std=c++11`. As with GNU `libstdc++`,
you need to explicitly turn on exceptions or RTTI support. For information on
how to do this, see [C++ Exceptions](#c_exceptions) and [RTTI](#rtti).

The NDK provides prebuilt static and shared libraries for `libc++`, but you can
force the NDK to rebuild `libc++` from sources by adding the following line to
your `Application.mk` file, or setting it in your environment prior to building:

```makefile
LIBCXX_FORCE_REBUILD := true
```

#### Atomic Support

If you include `<atomic>`, it's likely that you also need `libatomic`, If you
are using `ndk-build`, add the following line:

```makefile
LOCAL_LDLIBS += -latomic
```

If you are using your own toolchain, use:

```bash
-latomic
```

#### Compatibility

The NDK's libc++ is not stable. Not all the tests pass, and the test suite is
not comprehensive.  Some known issues are:

 * Support for `wchar_t` and the locale APIs is limited.

You should also make sure to check the "Known Issues" section of the changelog
for the NDK release you are using.

Warning: Attempting to change to an unsupported locale will **not** fail. The
operation will succeed, but the locale will not change and the following message
will appear in `logcat`.

```
newlocale() WARNING: Trying to set locale to en_US.UTF-8 other than "", "C" or "POSIX"
```


## Important Considerations
<a id="ic"></a>

### C++ Exceptions
<a id="xp"></a>

The NDK toolchain allows you to use C++ runtimes that support exception
handling. However, to ensure compatibility with earlier releases, it compiles
all C++ sources with `-fno-exceptions` support by default. You can enable C++
exceptions either for your entire app, or for individual modules.

To enable exception-handling support, add the following to your module-level
`build.gradle` file:

```gradle
android {
  ...
  defaultConfig {
    ...
    externalNativeBuild {

      // For ndk-build, instead use ndkBuild {}
      cmake {
        // Enables exception-handling support.
        cppFlags "-fexceptions"
      }
    }
  }
}
...
```

Alternatively, if you're using ndk-build, enable support for your entire app
by adding the following line to your [Application.mk] file:

```makefile
APP_CPPFLAGS := -fexceptions
```

To enable exception-handling support per individual modules while using
ndk-build, add the following line to their respective [Android.mk] files:

```makefile
LOCAL_CPP_FEATURES := exceptions
```

Alternatively, you can use:

```makefile
LOCAL_CPPFLAGS := -fexceptions
```

### RTTI
<a id="rt"></a>

The NDK toolchain allows you to use C++ runtimes that support RTTI. However, to
ensure compatibility with earlier releases, it compiles all C++ sources with
`-fno-rtti` by default.

To enable RTTI support, add the following to your module-level `build.gradle`
file:

```gradle
android {
  ...
  defaultConfig {
    ...
    externalNativeBuild {

      // For ndk-build, instead use ndkBuild {}
      cmake {
        // Enables RTTI support.
        cppFlags "-frtti"
      }
    }
  }
}
...
```

Alternatively, if you are using ndk-build, enable RTTI support for your
entire app by adding the following line to your [Application.mk] file.

```makefile
APP_CPPFLAGS := -frtti
```

To enable RTTI support for individual modules, add the following line to their
respective [Android.mk] files:

```makefile
LOCAL_CPP_FEATURES := rtti
```

Alternatively, you can use:

```makefile
LOCAL_CPPFLAGS := -frtti
```

### Static runtimes
<a id="sr"></a>

Linking the static library variant of a C++ runtime to more than one binary may
result in unexpected behavior. For example, you may experience:

 * Memory allocated in one library, and freed in the other, causing memory
   leakage or heap corruption.
 * Exceptions raised in `libfoo.so` going uncaught in `libbar.so`, causing your
   app to crash.
 * Buffering of `std::cout` not working properly.

In addition, if you link two shared libraries - or a shared library and an
executable - against the same static runtime, the final binary image of each
shared library includes a copy of the runtime's code. Having multiple instances
of runtime code is problematic because of duplication of certain global
variables that the runtime uses or provides internally.

This problem does not apply to a project comprising a single shared library. For
example, you can link against `stlport_static`, and expect your app to behave
correctly. If your project requires several shared library modules, we recommend
that you use the shared library variant of your C++ runtime.

### Shared runtimes

If your app targets a version of Android earlier than Android 4.3 (Android API
level 18), and you use the shared library variant of a given C++ runtime, you
must load the shared library before any other library that depends on it.

For example, an app may have the following modules:

 * libfoo.so
 * libbar.so which is used by libfoo.so
 * libstlport\_shared.so, used by both libfoo and libbar

You must load the libraries in reverse dependency order:

```java
    static {
      System.loadLibrary("stlport_shared");
      System.loadLibrary("bar");
      System.loadLibrary("foo");
    }
```

Note: Do not use the `lib` prefix when calling `System.loadLibrary()`.


## Licensing
<a id="li"></a>

STLport is licensed under a BSD-style open-source license. See
`$NDK/sources/cxx-stl/stlport/README` for more details about STLport.

GNU libstdc++ is covered by the GPLv3 license, and *not* the LGPLv2 or LGPLv3.
For more information, see
[License](http://gcc.gnu.org/onlinedocs/libstdc++/manual/license.html) on the
GCC website.

[LLVM libc++](https://llvm.org/svn/llvm-project/libcxx/trunk/LICENSE.TXT) is
dual-licensed under both the University of Illinois "BSD-Like" license and the
MIT license.

[Android.mk]: /ndk/guides/android_mk.html
[Application.mk]: /ndk/guides/application_mk.html
