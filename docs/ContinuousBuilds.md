Continuous Builds
=================

The NDK's continuous builds can be accessed by anyone with a Google account at
http://partner.android.com/build. Select "Build List" from the menu on the left
and then choose a branch and target from the menus at the top of the page. Note
that the "product" defaults to the macOS download, so if you're using Linux or
Windows you'll need to change that combo box too.

**Disclaimer**: These builds are **not** suitable for production use. This is
just a continuous build. The amount of testing these builds have been put
through is minimal. A successful build only means that our test suite *built*
successfully on Linux and Darwin. Windows is not covered (the Windows build bots
are actually Linux), and none of the tests have actually been run yet.


NDK Branches
------------

### NDK Canary

This is the master (development) branch of the NDK. Corresponds to
https://android.googlesource.com/platform/manifest/+/master-ndk.

### NDK rSOMETHING Release

Release branches of the NDK. Note that the actual released versions are not
tagged, but you can find the build number for the official release by examining
the source.properties file in your NDK. The `Pkg.Revision` entry is in the
format MAJOR.MINOR.BUILD (with beta or canary information being appended if
appropriate).


Current Issues
--------------

 * Ignore the `win64_${ARCH}` builds. Those shouldn't be in the list any more.
   You want `win64`.
 * If a given build was unsuccessful, the download link will be replaced with
   "BUILD\_ERROR.LOG", which is not a valid link for non-Googlers (logs access
   is restricted for security reasons). That link will, somewhat surprisingly,
   take you back to the main page.
