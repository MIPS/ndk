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


NDK r16
-------

Estimated release: Q3 2017

### Fixed libandroid\_support

As you are all well aware, early versions of Android were lacking a significant
number of libc APIs. libc++ requires some APIs that were not available until
android-21. To make libc++ available for all supported API levels, the NDK
provides `libandroid_support`.

`libandroid_support` is a collection of out of date Bionic sources mingled with
some musl sources and some home grown sources. This collection is statically
linked into any library you build with libc++ so that you'll always have an
implementation regardless of what API level you end up running on.

While a good idea, the current implementation is not good. This library is the
reason libc++ in the NDK carries hefty warning labels. The solution to this is
to start fresh with up to date Bionic sources. As with the unified headers,
these will actually be built directly from Bionic, so bug fixes to the platform
will automatically reach the NDK as well.

With this project finished, libc++ will be safe to use. At this point we will
begin recommending that developers move to libc++. Note that we will not change
the default STL in this release.

Note that `libandroid_support` will require unified headers. There are simply
too many discrepancies between the old headers and the new ones to make
`libandroid_support` work with both (`libandroid_support` is a bit more
complicated than a typical library in this because because it is actually the
implementation of a lot of these headers).

### Remove deprecated headers

Assuming that r15 switching to unified headers by default went well, we'll be
removing the deprecated headers in r16. If r15 turns up many issues, this will
be pushed to r17.


NDK r17
-------

Estimated release: Q4 2017

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

Estimated release: Q1 2018

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

Estimated release: Q2 2018

### Make standalone toolchains obsolete

Now that the NDK is down to a single compiler and STL, if we just taught the
Clang driver to emit `-D__ANDROID_API__=foo` and to link libc.so.18 instead of
libc.so, standalone toolchains would be obsolete because the compiler would
already be a standalone toolchain. The NDK toolchain would Just Work regardless
of build system, and the logic contained in each build system could be greatly
reduced.
