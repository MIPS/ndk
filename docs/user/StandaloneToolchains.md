Standalone Toolchains
=====================

You can use the toolchains provided with the Android NDK independently, or as
plug-ins with an existing IDE. This flexibility can be useful if you already
have your own build system, and only need the ability to invoke the
cross-compiler in order to add support to Android for it.

A typical use case is invoking the configure script of an open-source library
that expects a cross-compiler in the `CC` environment variable.

<p class="note">
<strong>Note:</strong> This page assumes significant understanding of compiling,
linking, and low-level architecture. In addition, the techniques it describes
are unnecessary for most use cases. In most cases, we recommend that you forego
using a standalone toolchain, and instead stick to the NDK build system.
</p>

Selecting Your Toolchain
------------------------

Before anything else, you need to decide which processing architecture your
standalone toolchain is going to target. Each architecture corresponds to a
different toolchain name, as Table 1 shows.

**Table 1.** `APP_ABI` settings for different instruction sets.

| Architecture | Toolchain name                         |
| ------------ | -------------------------------------- |
| ARM-based    | `arm-linux-androideabi-<gcc-version>`  |
| x86-based    | `x86-<gcc-version>`                    |
| MIPS-based   | `mipsel-linux-android-<gcc-version>`   |
| ARM64-based  | `aarch64-linux-android-<gcc-version>`  |
| X86-64-based | `x86_64-<gcc-version>`                 |
| MIPS64-based | `mips64el-linux-android-<gcc-version>` |

Selecting Your Sysroot
----------------------

The next thing you need to do is define your sysroot (A sysroot is a directory
containing the system headers and libraries for your target). To define the
sysroot, you must must know the Android API level you want to target for native
support; available native APIs vary by Android API level.

Native APIs for the respective [Android API levels] reside under
`$NDK/platforms/`; each API-level directory, in turn, contains subdirectories
for the various CPUs and architectures. The following example shows how to
define a sysroot> for a build targeting Android 5.0 (API level 21), for ARM
architecture:

```
SYSROOT=$NDK/platforms/android-21/arch-arm
```

For more detail about the Android API levels and the respective native APIs they
support, see [Native APIs](stable_apis.html).

[Android API levels]: https://developer.android.com/guide/topics/manifest/uses-sdk-element.html

Invoking the Compiler
---------------------

There are two ways to invoke the compiler. One method is simple, and leaves most
of the lifting to the build system. The other is more advanced, but provides
more flexibility.

### Simple method

The simplest way to build is by invoking the appropriate compiler directly from
the command line, using the `--sysroot` option to indicate the location of the
system files for the platform you're targeting. For example:

```bash
export CC="$NDK/toolchains/arm-linux-androideabi-4.8/prebuilt/ \
    linux-x86/bin/arm-linux-androideabi-gcc-4.8 --sysroot=$SYSROOT"
$CC -o foo.o -c foo.c
```

While this method is simple, it lacks in flexibility: It does not allow you to
use any C++ STL (STLport, libc++, or the GNU libstdc++) with it. It also does
not support exceptions or RTTI.

For Clang, you need to perform an additional two steps:

1. Add the appropriate `-target` for the target architecture, as Table 2 shows.

   | Architecture | Value                                    |
   | ------------ | ---------------------------------------- |
   | armeabi      | `-target armv5te-none-linux-androideabi` |
   | armeabi-v7a  | `-target armv7-none-linux-androideabi`   |
   | arm64-v8a    | `-target aarch64-none-linux-android`     |
   | x86          | `-target i686-non-linux-android`         |
   | x86\_64      | `-target x86_64-none-linux-android`      |
   | mips         | `-target mipsel-none-linux-android`      |

2. Add assembler and linker support by adding the `-gcc-toolchain` option, as in
   the following example:

       -gcc-toolchain $NDK/toolchains/arm-linux-androideabi-4.8/prebuilt/linux-x86_64

Ultimately, a command to compile using Clang might look like this:

```bash
export CC="$NDK/toolchains/arm-linux-androideabi-4.8/prebuilt/ \
    linux-x86/bin/arm-linux-androideabi-gcc-4.8 --sysroot=$SYSROOT \
    -target armv7-none-linux-androideabi \
    -gcc-toolchain $NDK/toolchains/arm-linux-androideabi-4.8/prebuilt/linux-x86_64"
$CC -o foo.o -c foo.c
```

### Advanced method

The NDK provides the `make-standalone-toolchain.sh` shell script to allow you to
perform a customized toolchain installation from the command line. This approach
affords you more flexibility than the procedure described in [Simple
method](#simple-method).

The script is located in the `$NDK/build/tools/` directory, where `$NDK` is the
installation root for the NDK. An example of the use of this script appears
below:

```bash
$NDK/build/tools/make-standalone-toolchain.sh \
--arch=arm --platform=android-21 --install-dir=/tmp/my-android-toolchain
```

This command creates a directory named `/tmp/my-android-toolchain/`, containing
a copy of the `android-21/arch-arm` sysroot, and of the toolchain binaries for a
32-bit ARM architecture.

Note that the toolchain binaries do not depend on or contain host-specific
paths, in other words, you can install them in any location, or even move them
if you need to.

By default, the build system uses the 32-bit, ARM-based GCC 4.8 toolchain. You
can specify a different value, however, by specifying `--arch=<toolchain>` as an
option.  Table 3 shows the values to use for other toolchains:

**Table 3.** Toolchains and corresponding values, using `--arch`.

| Toolchain                | Value           |
| ------------------------ | --------------- |
| mips64 compiler          | `--arch=mips64` |
| mips GCC 4.8 compiler    | `--arch=mips`   |
| x86 GCC 4.8 compiler     | `--arch=x86`    |
| x86\_64 GCC 4.8 compiler | `--arch=x86_64` |
| mips GCC 4.8 compiler    | `--arch=mips`   |

Alternatively, you can use the `--toolchain=<toolchain>` option. Table 4 shows
the values you can specify for `<toolchain>`:

**Table 4.** Toolchains and corresponding values, using `--toolchain`.

<table>
  <tr>
    <th scope="col">Toolchain</th>
    <th scope="col">Value</th>
  </tr>

  <tr>
    <td>arm</td>
    <td>
       <li>--toolchain=arm-linux-androideabi-4.8</li>
       <li>--toolchain=arm-linux-androideabi-4.9</li>
       <li>--toolchain=arm-linux-android-clang3.5</li>
       <li>--toolchain=arm-linux-android-clang3.6</li>
    </td>
  </tr>
  <tr>
    <td>x86</td>
    <td>
       <li>--toolchain=x86-linux-android-4.8</li>
       <li>--toolchain=x86-linux-android-4.9</li>
       <li>--toolchain=x86-linux-android-clang3.5</li>
       <li>--toolchain=x86-linux-android-clang3.6</li>
    </td>
  </tr>
  <tr>
    <td>mips</td>
    <td>
       <li>--toolchain=mips-linux-android-4.8</li>
       <li>--toolchain=mips-linux-android-4.9</li>
       <li>--toolchain=mips-linux-android-clang3.5</li>
       <li>--toolchain=mips-linux-android-clang3.6</li>
    </td>
  </tr>

  <tr>
    <td>arm64</td>
    <td>
       <li>--toolchain=aarch64-linux-android-4.9</li>
       <li>--toolchain=aarch64-linux-android-clang3.5</li>
       <li>--toolchain=aarch64-linux-android-clang3.6</li>
    </td>
  </tr>
  <tr>
    <td>x86_64</td>
    <td>
       <li>--toolchain=x86_64-linux-android-4.9</li>
       <li>--toolchain=x86_64-linux-android-clang3.5</li>
       <li>--toolchain=x86_64-linux-android-clang3.6</li>
    </td>
  </tr>
  <tr>
    <td>mips64</td>
    <td>
       <li>--toolchain=mips64el-linux-android-4.9</li>
       <li>--toolchain=mips64el-linux-android-clang3.5</li>
       <li>--toolchain=mips64el-linux-android-clang3.6</li>
    </td>
  </tr>
</table>

<p class="note">
<strong>Note:</strong> Table 4 is not an exhaustive list. Other combinations may
also be valid, but are unverified.
</p>

You can also copy Clang/LLVM 3.6, using one of two methods: You can append
`-clang3.6` to the `--toolchain` option, so that the `--toolchain` option looks
like the following example:

```bash
--toolchain=arm-linux-androideabi-clang3.6
```

You can also add `-llvm-version=3.6` as a separate option on the command line.

<p class="note">
<strong>Note:</strong> Instead of specifying a specific version, you can also use
`<version>`, which defaults to the highest available version of Clang.
</p>

By default, the build system builds for a 32-bit host toolchain. You can specify
a 64-bit host toolchain instead. Table 5 shows the value to use with `-system`
for different platforms.

**Table 5.** Host toolchains and corresponding values, using `-system`.

| Host toolchain  | Value                     |
| --------------- | ------------------------- |
| 64-bit Linux    | `--system=linux-x86_64`   |
| 64-bit Mac OS X | `--system=darwin-x86_64`  |
| 64-bit Windows  | `--system=windows-x86_64` |

For more information on specifying a 64- or 32-bit instruction host toolchain,
see [64-bit and 32-bit Toolchains](ndk-build.html#6432).

You may specify `--stl=stlport` to copy `libstlport` instead of the default
`libgnustl`. If you do so, and you wish to link against the shared library, you
must explicitly use `-lstlport_shared`. This requirement is similar to having to
use `-lgnustl_shared` for GNU `libstdc++`.

Similarly, you can specify `--stl=libc++` to copy the LLVM libc++ headers and
libraries.  To link against the shared library, you must explicitly use
`-lc++_shared`.

You can make these settings directly, as in the following example:

```bash
export PATH=/tmp/my-android-toolchain/bin:$PATH
export CC=arm-linux-androideabi-gcc   # or export CC=clang
export CXX=arm-linux-androideabi-g++  # or export CXX=clang++
```

Note that if you omit the `-install-dir` option, the
`make-standalone-toolchain.sh` shell script creates a tarball in
`tmp/ndk/<toolchain-name>.tar.bz2`. This tarball makes it easy to archive, as
well as to redistribute the binaries.

This standalone toolchain provides an additional benefit, as well, in that it
contains a working copy of a C++ STL library, with working exceptions and RTTI
support.

For more options and details, use `--help`.

Working with Clang
------------------

You can install Clang binaries in the standalone installation by using the
`--llvm-version=<version>` option. `<version>` is a LLVM/Clang version number,
such as `3.5` or `3.6`. For example:

```bash
build/tools/make-standalone-toolchain.sh \
    --install-dir=/tmp/mydir \
    --toolchain=arm-linux-androideabi-4.8 \
    --llvm-version=3.6
```

Note that Clang binaries are copied along with the GCC ones, because they rely
on the same assembler, linker, headers, libraries, and C++ STL implementation.

This operation also installs two scripts, named `clang` and `clang++`, under
`<install-dir>/bin/@`. These scripts invoke the real `clang` binary with default
target architecture flags. In other words, they should work without any
modification, and you should be able to use them in your own builds by just
setting the `CC` and `CXX` environment variables to point to them.

Invoking Clang
--------------

In an ARM standalone installation built with `llvm-version=3.6`, invoking
[Clang](http://clang.llvm.org) on a Unix system takes the form of a single line.
For instance:

```bash
`dirname $0`/clang36 -target armv5te-none-linux-androideabi "$@"
```

`clang++` invokes `clang++31` in the same way.

#### Clang targets with ARM

When building for ARM, Clang changes the target based on the presence of the
`-march=armv7-a` and/or `-mthumb` options:

**Table 5.** Specifiable `-march` values and their resulting targets.

| `-march` value                      | Resulting target                 |
| ----------------------------------- | -------------------------------- |
| `-march=armv7-a`                    | `armv7-none-linux-androideabi`   |
| `-mthumb`                           | `thumb-none-linux-androideabi`   |
| Both `-march=armv7-a` and `-mthumb` | `thumbv7-none-linux-androideabi` |

You may also override with your own `-target` if you wish.

The `-gcc-toolchain` option is unnecessary because, in a standalone package,
Clang locates `as` and `ld` in a predefined relative location.

`clang` and `clang++` should be easy drop-in replacements for `gcc` and `g++` in
a makefile. When in doubt, add the following options to verify that they are
working properly:

* `-v` to dump commands associated with compiler driver issues
* `-###` to dump command line options, including implicitly predefined ones.
* `-x c < /dev/null -dM -E` to dump predefined preprocessor definitions
* `-save-temps` to compare `*.i` or `*.ii` preprocessed files.

For more information about Clang, see http://clang.llvm.org/, especially the GCC
compatibility section.


ABI Compatibility
-----------------

The machine code that the ARM toolchain generates should be compatible with the
official Android `armeabi` [ABI](abis.html) by default.

We recommend use of the `-mthumb` compiler flag to force the generation of
16-bit Thumb-1 instructions (the default being 32-bit ARM instructions).

If you want to target the armeabi-v7a ABI, you must set the following flags:

```
CFLAGS= -march=armv7-a -mfloat-abi=softfp -mfpu=vfpv3-d16
```

The first flag enables Thumb-2 instructions. The second flag enables
hardware-FPU instructions while ensuring that the system passes floating-point
parameters in core registers, which is critical for ABI compatibility.

<p class="note">
<strong>Note:</strong> In versions of the NDK prior to r9b, do not use these
flags separately. You must set all or none of them. Otherwise, unpredictable
behavior and crashes may result.
</p>

To use NEON instructions, you must change the `-mfpu` compiler flag:

```
CFLAGS= -march=armv7-a -mfloat-abi=softfp -mfpu=neon
```

Note that this setting forces the use of `VFPv3-D32`, per the ARM specification.

Also, make sure to provide the following two flags to the linker:

```
LDFLAGS= -march=armv7-a -Wl,--fix-cortex-a8
```

The first flag instructs the linker to pick `libgcc.a`, `libgcov.a`, and
`crt*.o`, which are tailored for armv7-a. The 2nd flag is required as a
workaround for a CPU bug in some Cortex-A8 implementations.

Since NDK version r9b, all Android native APIs taking or returning double or
float values have `attribute((pcs("aapcs")))` for ARM. This makes it possible to
compile user code in `-mhard-float` (which implies `-mfloat-abi=hard`), and
still link with the Android native APIs that comply with the softfp ABI. For
more information on this, see the comments in
`$NDK/tests/device/hard-float/jni/Android.mk`.

If you want to use NEON intrinsics on x86, the build system can translate them
to the native x86 SSE intrinsics using a special C/C++ language header with the
same name, `arm_neon.h`, as the standard ARM NEON intrinsics header.

By default, the x86 ABI supports SIMD up to SSSE3, and the header covers ~93% of
(1869 of 2009) NEON functions.

You don't have to use any specific compiler flag when targeting the MIPS ABI.

To learn more about ABI support, see [x86 Support](x86.html).

Warnings and Limitations
------------------------

### Windows support

The Windows binaries do not depend on Cygwin. This lack of dependency makes them
faster. The cost, however, is that they do not understand Cygwin path
specifications like `cygdrive/c/foo/bar`, as opposed to `C:/foo/bar`.

The NDK build system ensures that all paths passed to the compiler from Cygwin
are automatically translated, and manages other complexities, as well. If you
have a custom build system, you may need to resolve these complexities yourself.

For information on contributing to support for Cygwin/MSys, visit the
[android-ndk forum](https://groups.google.com/forum/#!forum/android-ndk).

### `wchar_t` support

The Android platform did not really support `wchar_t` until Android 2.3 (API
level 9). This fact has several ramifications:

* If you target platform Android 2.3 or higher, the size of `wchar_t` is 4
  bytes, and most `wide-char` functions are available in the C library (with the
  exception of multi-byte encoding/decoding functions and `wsprintf`/`wsscanf`).

* If you target any lower API level, the size of `wchar_t` is 1 byte, and none
  of the wide-char functions works.

We recommend that you get rid of any dependencies on the `wchar_t` type, and
switch to better representations. The support provided in Android is only there
to help you migrate existing code.

### Exceptions, RTTI, and STL

The toolchain binaries support C++ exceptions and RTTI by default. To disable
C++ exceptions and RTTI when building sources (to generate lighter-weight
machine code, for example), use `-fno-exceptions` and `-fno-rtti`.

To use these features in conjunction with GNU libstdc++, you must explicitly
link with libsupc++.  To do so, use `-lsupc++` when linking binaries. For
example:

```bash
arm-linux-androideabi-g++ .... -lsupc++
```

You do not need to do this when using the STLport or libc++ library.

### C++ STL support

The standalone toolchain includes a copy of a C++ Standard Template Library
implementation. This implementation is either for GNU libstdc++, STLport, or
libc++, depending on what you specify for the `--stl=<name>` option described
previously. To use this implementation of STL, you need to link your project
with the proper library:

* Use `-lstdc++` to link against the static library version of any
  implementation. Doing so ensures that all required C++ STL code is included
  into your final binary. This method is ideal if you are only generating a
  single shared library or executable.

  This is the method that we recommend.

* Alternatively, use `-lgnustl_shared` to link against the shared library
  version of GNU `libstdc++`. If you use this option, you must also make sure to
  copy `libgnustl_shared.so` to your device in order for your code to load
  properly. Table 6 shows where this file is for each toolchain type.

  <p class="note">
  <strong>Note:</strong> GNU libstdc++ is licensed under the GPLv3 license, with
  a linking exception. If you cannot comply with its requirements, you cannot
  redistribute the shared library in your project.
  </p>


* Use `-lstlport_shared` to link against the shared library version of STLport.
  When you do so, you need to make sure that you also copy
  `libstlport_shared.so` to your device in order for your code to load properly.
  Table 6 shows where this file is for each toolchain:

  **Table 6.** Specifiable `-march` values and their resulting targets.

  | Toolchain | Location                                 |
  | --------- | ---------------------------------------- |
  | arm       | `$TOOLCHAIN/arm-linux-androideabi/lib/`  |
  | arm64     | `$TOOLCHAIN/aarch64-linux-android/lib/`  |
  | x86       | `$TOOLCHAIN/i686-linux-android/lib/`     |
  | x86\_64   | `$TOOLCHAIN/x86_64-linux-android/lib/`   |
  | mips      | `$TOOLCHAIN/mipsel-linux-android/lib/`   |
  | mips64    | `$TOOLCHAIN/mips64el-linux-android/lib/` |

<p class="note">
<strong>Note:</strong> If your project contains multiple shared libraries or
executables, you must link against a shared-library STL implementation.
Otherwise, the build system does not define certain global uniquely, which can
result in unpredictable runtime behavior.  This behavior may include crashes and
failure to properly catch exceptions.
</p>

The reason the shared version of the libraries is not simply called
`libstdc++.so` is that this name would conflict at runtime with the system's own
minimal C++ runtime. For this reason, the build system enforces a new name for
the GNU ELF library. The static library does not have this problem.
