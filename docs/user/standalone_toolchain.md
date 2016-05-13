Standalone Toolchains
=====================

You can use the toolchains provided with the Android NDK independently or as
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

Before anything else, you need to decide which processor architecture your
standalone toolchain is going to target. Each architecture corresponds to a
different toolchain name, as Table 1 shows.

**Table 1.** Toolchain names for different instruction sets.

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

The next thing you need to do is define your sysroot. A sysroot is a directory
containing the system headers and libraries for your target. To define the
sysroot, you must must know the Android API level you want to target for native
support; available native APIs vary by Android API level.

Native APIs for the respective [Android API levels] reside under
`$NDK/platforms/`; each API-level directory, in turn, contains subdirectories
for the various CPUs and architectures.

For more detail about the Android API levels and the respective native APIs they
support, see [Native APIs](stable_apis.html).

[Android API levels]: https://developer.android.com/guide/topics/manifest/uses-sdk-element.html

Creating the Toolchain
----------------------

The NDK provides the `make_standalone_toolchain.py` script to allow you to
perform a customized toolchain installation from the command line.

This is a new tool that replaces the old `make-standalone-toolchain.sh`. It has
been reimplented in Python so that Windows users will not need to install Cygwin
or MSys to take advantage of this tool.

The script is located in the `$NDK/build/tools/` directory, where `$NDK` is the
installation root for the NDK.

An example of the use of this script appears below:

```bash
$NDK/build/tools/make_standalone_toolchain.py \
    --arch arm --api 21 --install-dir /tmp/my-android-toolchain
```

This command creates a directory named `/tmp/my-android-toolchain/`, containing
a copy of the `android-21/arch-arm` sysroot, and of the toolchain binaries for a
32-bit ARM architecture.

Note that the toolchain binaries do not depend on or contain host-specific
paths. In other words, you can install them in any location or even move them if
you need to.

The `--arch` arugment is required, but the STL will default to gnustl and the
API level will be set to the minimum supported level for the given architecture
(currently 9 for 32-bit architectures and 21 for 64-bit architectures) if not
explicitly stated.

Unlike the old tool, Clang is always copied into the toolchain. Every standalone
toolchain is useable for both Clang and GCC.

You may specify `--stl=stlport` to copy `libstlport` instead of the default
`libgnustl`. If you do so, and you wish to link against the shared library, you
must explicitly use `-lstlport_shared`. This requirement is similar to having to
use `-lgnustl_shared` for GNU `libstdc++`.

Similarly, you can specify `--stl=libc++` to copy the LLVM libc++ headers and
libraries.  To link against the shared library, you must explicitly use
`-lc++_shared`. As mentioned in [C++ Library Support](cpp-support.html), you
will often need to pass `-latomic` when linking against libc++.

You can make these settings directly, as in the following example:

```bash
export PATH=/tmp/my-android-toolchain/bin:$PATH
export CC=arm-linux-androideabi-gcc   # or export CC=clang
export CXX=arm-linux-androideabi-g++  # or export CXX=clang++
```

Note that if you omit the `--install-dir` option, the tool creates a tarball in
the current directory named `$TOOLCHAIN_NAME.tar.bz2`. The tarball can be placed
in a different directory by using `--package-dir`.

For more options and details, use `--help`.

Working with Clang
------------------

Clang binaries are automatically included in standalone toolchains created with
the new tool.

Note that Clang binaries are copied along with the GCC ones, because they rely
on the same assembler, linker, headers, libraries, and C++ STL implementation.

This operation also installs two scripts, named `clang` and `clang++`, under
`<install-dir>/bin`. These scripts invoke the real `clang` binary with the
correct target architecture flags. In other words, they should work without any
modification, and you should be able to use them in your own builds by just
setting the `CC` and `CXX` environment variables to point to them.

### Clang targets with ARM

When building for ARM, Clang changes the target based on the presence of the
`-march=armv7-a` and/or `-mthumb` options:

**Table 2.** Specifiable `-march` values and their resulting targets.

| `-march` value                      | Resulting target                 |
| ----------------------------------- | -------------------------------- |
| `-march=armv7-a`                    | `armv7-none-linux-androideabi`   |
| `-mthumb`                           | `thumb-none-linux-androideabi`   |
| Both `-march=armv7-a` and `-mthumb` | `thumbv7-none-linux-androideabi` |

You may also override with your own `-target` if you wish.

The `-gcc-toolchain` option is unnecessary in a standalone toolchain because
Clang locates `as` and `ld` in a predefined relative location.

`clang` and `clang++` should be drop-in replacements for `gcc` and `g++` in a
makefile. When in doubt, add the following options to verify that they are
working properly:

* `-v` to dump commands associated with compiler driver issues
* `-###` to dump command line options, including implicitly predefined ones.
* `-x c < /dev/null -dM -E` to dump predefined preprocessor definitions
* `-save-temps` to compare `*.i` or `*.ii` preprocessed files.

For more information about Clang, see http://clang.llvm.org/, especially the GCC
compatibility section.

ABI Compatibility
-----------------

By default, an ARM Clang standalone toolchain will target the armeabi-v7a ABI.
GCC will target armeabi. Either can be controlled by passing the appropriate
`-march` flag, and Clang can also be controlled with `-target`.

To target armeabi-v7a with GCC, you must set the following flags:

```
CFLAGS= -march=armv7-a -mfloat-abi=softfp -mfpu=vfpv3-d16
```

The first flag targets the armv7 architecture. The second flag enables
hardware-FPU instructions while ensuring that the system passes floating-point
parameters in core registers, which is critical for ABI compatibility.

We recommend using the `-mthumb` compiler flag to force the generation of
16-bit Thumb-2 instructions (Thumb-1 for armeabi). If omitted, the toolchain
will emit 32-bit ARM instructions.

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

You don't have to use any specific compiler flag when targeting the other ABIs.

To learn more about ABI support, see [ABIs](abis.html).

Warnings and Limitations
------------------------

### Windows support

The Windows binaries do not depend on Cygwin. This lack of dependency makes them
faster. The cost, however, is that they do not understand Cygwin path
specifications like `cygdrive/c/foo/bar`, as opposed to `C:/foo/bar`.

The NDK build system ensures that all paths passed to the compiler from Cygwin
are automatically translated, and manages other complexities, as well. If you
have a custom build system, you may need to resolve these complexities yourself.

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

  **Table 3.** Specifiable `-march` values and their resulting targets.

  | Toolchain | Location                                 |
  | --------- | ---------------------------------------- |
  | arm       | `$TOOLCHAIN/arm-linux-androideabi/lib/`  |
  | arm64     | `$TOOLCHAIN/aarch64-linux-android/lib/`  |
  | mips      | `$TOOLCHAIN/mipsel-linux-android/lib/`   |
  | mips64    | `$TOOLCHAIN/mips64el-linux-android/lib/` |
  | x86       | `$TOOLCHAIN/i686-linux-android/lib/`     |
  | x86\_64   | `$TOOLCHAIN/x86_64-linux-android/lib/`   |

<p class="note">
<strong>Note:</strong> If your project contains multiple shared libraries or
executables, you must link against a shared-library STL implementation.
Otherwise global state in these libraries will not be unique, which can result
in unpredictable runtime behavior. This behavior may include crashes and
failure to properly catch exceptions.
</p>

The reason the shared version of the libraries is not simply called
`libstdc++.so` is that this name would conflict at runtime with the system's own
minimal C++ runtime. For this reason, the build system enforces a new name for
the GNU ELF library. The static library does not have this problem.
