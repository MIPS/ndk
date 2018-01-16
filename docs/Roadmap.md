NDK Roadmap
===========

**Note**: If there's anything you want to see done in the NDK, [file a bug]!
Nothing here is set in stone, and if there's something that we haven't thought
of that would be of more use, we'd be happy to adjust our plans for that.

[file a bug]: https://github.com/android-ndk/ndk/issues

**Disclaimer**: Everything here is subject to change. The further the plans are
in the future, the less stable they will be. Things in the upcoming release are
fairly certain, and the second release is quite likely. Beyond that, anything
written here is what we would like to accomplish in that release assuming things
have gone according to plan until then.

**Note**: For release timing, see our [release schedule] on our wiki.

[release schedule]: https://github.com/android-ndk/ndk/wiki#release-schedule


NDK r17
-------

Estimated release: Q1 2018

### Default to libc++

If NDK r16 shows that libc++ with the refreshed `libandroid_support` is working
well, the NDK will begin defaulting to using libc++. This means `ndk-build`,
CMake, the Gradle plugin, and standalone toolchains. We don't have any control
over other build systems :)

### Bugfix Release

With all the systemic NDK issues now solved (or at least pending feedback on the
attempted fixes), we should take a look through our bug backlog and start fixing
all the non-critical and nice-to-have issues.


NDK r18
-------

Estimated release: Q2 2018

### Remove non-libc++ STLs

libc++ has been the default for a release and has proven to be stable. It is a
strict improvement over the other STLs (more features, better Clang
compatibility, Apache licensed, most reliable). The fact that the NDK supports
multiple STLs is a common pain point for users (it's confusing for newcomers,
and it makes sharing libraries difficult because they must all use the same
STL).

Now that we have a good choice for a single STL, we'll remove the others. We'll
most likely move the source we have for these along with building instructions
to a separate project so that people that need these for ABI compatibility
reasons can continue using them, but support for these will end completely.

### Remove GCC

GCC is still in the NDK today because some of gnustl's C++11 features were
written such that they do not work with Clang (threading and atomics, mostly).
Now that libc++ is the best choice of STL, this is no longer blocking, so GCC
can be removed.

### Bugfix Release

The r17 release cycle alone probably won't be enough to burn down enough of
these issues.


NDK r19
-------

Estimated release: Q3 2018

### Make standalone toolchains obsolete

Now that the NDK is down to a single compiler and STL, if we just taught the
Clang driver to emit `-D__ANDROID_API__=foo` and to link libc.so.18 instead of
libc.so, standalone toolchains would be obsolete because the compiler would
already be a standalone toolchain. The NDK toolchain would Just Work regardless
of build system, and the logic contained in each build system could be greatly
reduced.


NDK r20+
--------

Estimated release: Q4 2018

### Better tools for improving code quality.

The NDK has long included `gtest` and clang supports various sanitiziers,
but there are things we can do to improve the state of testing/code quality:

  * Test coverage support.
  * Easier access to sanitizers (such as asan).
  * `clang-tidy`.

### Help building complex applications.

There are several well-known pain points for NDK users that we should
address.

The samples are low-quality and don't necessarily cover
interesting/difficult topics.

For serious i18n, `icu4c` is too big too bundle, and non-trivial to use
the platform. We have a C API wrapper prototype, but we need to make it
easily available for NDK users.

There are many other commonly-used libraries (such as BoringSSL) that
are currently difficult to build/package, let alone keep updated. We
should investigate using [cdep] to simplify this.

NDK APIs are C-only for ABI stability reasons. We should offer header-only
C++ wrappers for NDK APIs, even if only to offer the benefits of RAII.

[cdep]: https://github.com/jomof/cdep

### Unify CMake NDK Support Implementations

CMake added their own NDK support about the same time we added our toolchain
file. The two often conflict with each other, and a toolchain file is a messy
way to implement this support. However, fully switching to the integrated
support puts NDK policy deicisions (default options, NDK layout, etc) fully into
the hands of CMake, which makes them impossible to update without the user also
updating their CMake version.

We should send patches to the CMake implementation that will load as much
information about the NDK as possible from tables we provide in the NDK.


Historical releases
-------------------

Full [history] is available, but this section summarizes major changes
in recent releases.

[history]: https://developer.android.com/ndk/downloads/revision_history.html

### NDK r16

Fixed libandroid\_support, libc++ now the recommended STL (but still
not the default).

Removed non-unified headers.

### NDK r15

Defaulted to [unified headers] (opt-out).

Removed support for API levels lower than 14 (Android 4.0).

### NDK r14

Added [unified headers] (opt-in).

[unified headers]: https://android.googlesource.com/platform/ndk/+/master/docs/UnifiedHeaders.md

### NDK r13

Added [simpleperf].

[simpleperf]: https://developer.android.com/ndk/guides/simpleperf.html

### NDK r12

Removed [armeabi-v7a-hard].

Removed support for API levels lower than 9 (Android 2.3).

[armeabi-v7a-hard]: https://android.googlesource.com/platform/ndk/+/ndk-r12-release/docs/HardFloatAbi.md
