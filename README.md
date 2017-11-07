Android Native Development Kit (NDK)
====================================

The latest version of this document is available at
https://android.googlesource.com/platform/ndk/+/master/README.md.

**Note:** This document is for developers _of_ the NDK, not developers that use
the NDK.

The NDK allows Android application developers to include native code in their
Android application packages, compiled as JNI shared libraries.

[TOC]

Other Resources
---------------

 * User documentation is available on the [Android Developer website].
 * Discussions related to the Android NDK happen on the [android-ndk Google
   Group].
 * Announcements such as releases are posted to the [android-ndk-announce Google
   Group].
 * File bugs against the NDK at https://github.com/android-ndk/ndk/issues.

[Android Developer website]: https://developer.android.com/ndk/index.html
[android-ndk Google Group]: http://groups.google.com/group/android-ndk
[android-ndk-announce Google Group]: http://groups.google.com/group/android-ndk-announce

Building the NDK
================

Both Linux and Windows NDKs are built on Linux machines. Windows host binaries
are cross-compiled with MinGW.

Building the NDK for Mac OS X requires at least 10.8.

Components
----------

The NDK components can be loosely grouped into host toolchains, target
prebuilts, build systems, and support libraries.

### Host Toolchains

* `toolchains/` contains GCC and Clang toolchains.
    * `$TOOLCHAIN/config.mk` contains ARCH and ABIS this toolchain can handle.
    * `$TOOLCHAIN/setup.mk` contains toolchain-specific default CFLAGS/LDFLAGS
      when this toolchain is used.
* `prebuilt/$HOST_TAG` contains build dependencies and additional tools.
    * make, python, yasm, and for Windows: cmp.exe and echo.exe
    * `ndk-depends`, `ndk-stack` and `ndk-gdb` can also be found here.

### Target Prebuilts

* `sysroot/usr/include` contains the headers for the NDK. See [Unified Headers]
  for more information.
* `platforms/android-$VERSION/arch-$ARCH_NAME/` contains stub shared libraries
  and a few static libraries for each API level. See [Platform APIs] for more
  information.
* `sources/cxx-stl/$STL` contains the headers and libraries for the various C++
  STLs.
* `prebuilt/android-$ARCH/gdbserver` contains gdbserver.

[Unified Headers]: docs/UnifiedHeaders.md
[Platform APIs]: docs/PlatformApis.md

### Build Systems

* `build/` contains ndk-build, the NDK's home grown build system. Most of the
  implementation lives in `build/core`.
* `build/cmake` contains components for using the NDK with CMake (at present
  only a CMake toolchain file, but in the future it will contain CMake modules
  that CMake will load, obviating the need for a toolchain file).
* `build/tools` contains `make_standalone_toolchain.py`, but also contains
  legacy sripts that were used to build the NDK. Eventually, this should contain
  nothing but the standalone toolchain scripts.
* The gradle plugins for the NDK are not included in the NDK.

### Support Libraries

* `sources/android` and `sources/third_party` contain modules that can be used
  in apps (gtest, cpufeatures, native\_app\_glue, etc) via
  `$(call import-module,$MODULE)`.

Prerequisites
-------------

* [AOSP NDK Repository](http://source.android.com/source/downloading.html)
    * Check out the branch `master-ndk`

        ```bash
        repo init -u https://android.googlesource.com/platform/manifest \
            -b master-ndk

        # Googlers, use
        repo init -u \
            persistent-https://android.git.corp.google.com/platform/manifest \
            -b master-ndk
        ```

Linux dependencies are listed in the [Dockerfile]. You can use docker to build
the NDK:

```bash
docker build -t ndk-dev .
docker run -it -u $UID -v `realpath ..`:/src -w /src/ndk ndk-dev ./checkbuild.py
```

Building on Mac OS X has similar dependencies as Linux, but also requires Xcode.

Running tests requires that `adb` is in your `PATH`. This is provided as part of
the [Android SDK].

[Dockerfile]: infra/docker/Dockerfile
[Android SDK]: https://developer.android.com/studio/index.html#downloads

Building the NDK
----------------

### For Linux or Darwin:

```bash
$ python checkbuild.py
```

### For Windows, from Linux:

```bash
$ python checkbuild.py --system windows  # Or windows64.
```

`checkbuild.py` will also build all of the NDK tests. This takes about four
times as long as building the NDK itself, so pass `--no-build-tests` to skip
building the tests. They can be built later with `python run_tests.py
--rebuild`.

`checkbuild.py` also accepts a variety of other options to speed up local
builds, namely `--arch` and `--module`.

Packaging
---------

By default, `checkbuild.py` will also package the NDK. To skip the packaging
step, use the `--no-package` flag. To avoid packaging an incomplete NDK,
packaging will not be run if `--module` was passed unless `--force-package` was
also provided.
