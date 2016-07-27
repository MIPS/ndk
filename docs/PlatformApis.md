Platform APIs
=============

The latest version of this document is available at
https://android.googlesource.com/platform/ndk/+/master/docs/PlatformApis.md.

**Note:** This document covers the new method of getting platform APIs into the
NDK. For the time being, the old method is still in use as well, and is covered
by [Generating Sysroots](GeneratingSysroots.md).

For Platform Developers
-----------------------

To get your API into the NDK you'll generally need to define the two pieces that
implement it: the headers and the libraries. Often the library is libandroid.so
and you won't need to add a new library, but you'll need to modify an existing
one. For this reason, libraries and the headers for those libraries are defined
separately.

### Headers

To add headers to the NDK, create an `ndk_headers` module in your Android.bp.
Examples of this module type can be found in [bionic/libc/Android.bp].
TODO(danalbert): Actually migrate libc so that's true.

These module definitions are as follows:

```
// Will install $MODULE_PATH/include/foo/bar/baz.h to qux/bar/baz.h (relative to
// $NDK_OUT/sysroot/usr/include).
ndk_headers {
    name: "foo",

    // Base directory of the headers being installed. This path will be stripped
    // when installed.
    from: "include/foo",

    // Install path within the sysroot.
    to: "qux",

    // List of headers to install. Relative to the Android.bp. Glob compatible.
    // The common case is "include/**/*.h".
    srcs: ["include/foo/bar/baz.h"],
}
```

### Libraries

To add a library to the NDK, create an `ndk_library` module in your Android.bp.
An example of this module type can be found in [bionic/libc/Android.bp].
TODO(danalbert): Actually migrate libc so that's true.

These module defintions are as follows:

```
// The name of the generated file will be based on the module name by stripping
// the ".ndk" suffix from the module name. Module names must end with ".ndk"
// (as a convention to allow soong to guess the NDK name of a dependency when
// needed). "libfoo.ndk" will generate "libfoo.so.
ndk_library {
    name: "libfoo.ndk",

     A version script with some metadata that encodes version and arch
    // mappings so that only one script is needed instead of one per API/arch.
    // An example of this file can be found at [bionic/libc/libc.map.txt].
    // TODO(danalbert): Actually migrate libc so that example is correct.
    symbol_file: "libfoo.map.txt",

    // The first API level a library was available. A library will be generated
    // for every API level beginning with this one.
    first_version: "9",
}
```

### Inform the build system

The build system needs to know your library has been migrated to the new form so
it can get the libraries from the out directory instead of prebuilts/ndk.
Example CL: https://android-review.googlesource.com/#/c/251420/

Note that if you're migraring an existing library you'll also need to remove the
old prebuilt/ndk module. Here's an example of doing that for libc and libm:
https://android-review.googlesource.com/#/c/251420/ (and also the CL for running
the generator: https://android-review.googlesource.com/#/c/251441/).

A full topic of migrating libc and libm from prebuilts/ndk to `ndk_library` and
`ndk_headers` can be found here:
https://android-review.googlesource.com/#/q/topic:ndk_library-libc-libm

[bionic/libc/Android.bp]: https://android.googlesource.com/platform/bionic/+/master/libc/Android.bp

For NDK Developers
------------------

TODO(danalbert): Figure out how these get into the NDK build process.
