Testing the NDK
===============

The latest version of this document is available at
https://android.googlesource.com/platform/ndk/+/master/docs/Testing.md.

Testing Tools
-------------

There are currently three tools used in testing:

 1. `run_tests.py`, for testing a specific configuration.
 2. `validate.py`, for testing many configurations.
 3. `test_libcxx.py`, for testing libc++.

A test configuration is a tuple of (ABI, target platform, toolchain, device).

At some point the three of these will most likely merge into one script.

### Testing a Single Configuration: [run\_tests.py]

For targeted testing during development, `run_tests.py` can be used to verify a
single test configuration, as well as run specific tests.

Running the NDK tests requires a complete NDK package (see [README.md] for
building instructions).

[README.md]: ../README.md

From the NDK source directory (not the extracted package):

```bash
$ python run_tests.py --abi $ABI_TO_TEST
```

If you're testing a downloading NDK, the path to the NDK to test may optionally
be passed to `run-tests.py`. Otherwise the path will be assumed to be the
install location in the out directory.

The default toolchain for testing is Clang. To run the tests with GCC, use the
option `--toolchain 4.9`.

The full test suite includes tests which run on a device or emulator, so you'll
need to have `adb` in your path and `ANDROID_SERIAL` set if more than one
device/emulator is connected. If you do not have a device capable of running the
tests, you can run just the `build` or `awk` test suites with the `--suite`
flag.

### Testing Multiple Configurations: [validate.py]

When testing multiple configurations, `validate.py` will automatically detect
connected devices/emulators and choose a subset of them to fit our QA
configuration. This script will run all of the tests across all available ABIs
on several devices, and thus will take a long time (takes ~75 minutes on my
machine, even with a few configurations unavailable). As such, this isn't
suitable for active development, but should be run for QA and for any changes
that might have a wide impact (compiler updates, `ndk-build` changes, sysroot
changes, etc).

To use this script, connect any devices and launch any emulators you need for
testing (make sure ADB has authorization to control them), then run:

```bash
$ python validate.py
```

If you're testing a downloading NDK, the path to the NDK to test may optionally
be passed to `run-tests.py`. Otherwise the path will be assumed to be the
install location in the out directory.

By default, test logs will be placed in $PWD/test-logs. This can be controlled
with the `--log-dir` flag.

### Broken and Unsupported Tests

To mark tests as currently broken or as unsupported for a given configuration,
add a `test_config.py` to the test's root directory (in the same directory as
`jni/`).

Unsupported tests will not be built or run.

Broken tests will be built and run, and the result of the test will be inverted.
A test that fails will become an "EXPECTED FAILURE" and not be counted as a
failure, whereas a passing test will become an "UNEXPECTED SUCCESS" and count as
a failure.

By default, `run_tests.py` will hide expected failures from the output since the
user is most likely only interested in seeing what effect their change had. To
see the list of expected failures, pass `--show-all`.

Here's an example `test_config.py` that marks this test as broken when building
for arm64 and unsupported when running on a pre-Lollipop device:

```python
def build_broken(abi, platform, toolchain):
    if abi == 'arm64-v8a':
        return abi, 'https://github.com/android-ndk/ndk/issues/foo'
    return None, None

def run_unsupported(abi, device_api, toolchain, subtest):
    if device_api < 21:
        return device_api
    return None
```

The `_broken` checks return a tuple of `(broken_configuration, bug_url)` if the
given configuration is known to be broken, else `(None, None)`.

The `_unsupported` checks return `broken_configuration` if the given
configuration is unsupported, else `None`.

The configuration is specified by the following arguments:

* `abi`: The ABI being built for.
* `platform`: The platform version being *built* for. Not necessarily the
  platform version that the test will be run on. Can be `None`, in which case
  the default API level for that ABI should be considered.
* `device_platform`: The platform version of the device the test will be run on.
  Note that this parameter is ommitted for build tests. In a `--skip-run`
  configuration, this is set to the minimum supported API level for the given
  API (9 for LP32, 21 for LP64).
* `toolchain`: The toolchain being used. `'clang'` if we're using clang (the
  default), or `'4.9'` if we're using GCC.
* `subtest`: This is `None` for build tests and for the build step of device
  tests, but will be set to the name of the executable for the run step of
  device tests. If the test builds fine but fails at runtime, you must gate your
  check with this.

### Testing libc++: [test\_libcxx.py]

The libc++ tests are not currently integrated into the main NDK tests. To run
the libc++ tests:

```bash
$ ./test_libcxx.py --abi $ABI --platform $API_LEVEL
```

Note that these tests are far from failure free. In general, most of these test
failures are locale related and fail because we don't support anything beyond
the C locale.

Setting Up a Test Environment
-----------------------------

To run the NDK tests, you will need:

 * An NDK. The NDK doesn't necessarily need to contain support for every
   architecture.
 * `adb` in your path.
     * This is only needed if you're running device tests.
     * Always use the latest available version of `adb`. Note that the version
       of `adb` in the SDK manager might be surprisingly old. It's best to use a
       version built fresh from AOSP.
 * A device or emulator attached.
     * Again, only needed for device tests.

### Devices and Emulators

For testing a release, make sure you're testing against the released builds of
Android.

For Nexus devices, factory images are available here:
https://developers.google.com/android/nexus/images. Googlers, you may want to
use the flash station to get a userdebug image since that is needed for ASAN
testing. You should still make sure you also test on user builds because that is
what all of our users have.

For emulators, use emulator images from the SDK rather than from a platform
build. Again, these are what our users will be using.

After installing the emulator images from the SDK manager, they can be
configured and launched for testing with (assuming the SDK tools directory is in
your path):

```bash
$ android create avd --name $NAME --target android-$LEVEL --abi $ABI
$ emulator -avd $NAME -no-window -no-audio -no-skin
```

This will create a new virtual device and launch it in a headless state.

QA Configuration
----------------

The current configuration we use to test NDK releases is as written in
[qa\_config.yaml]:

Each API level/ABI pair will be checked with both Clang and GCC, unified and
deprecated headers.

Note that there are no ARM64 emulators whatsoever in the SDK manager. Testing
ARM64 will require a physical device.

[qa\_config.yaml]: ../qa_config.yaml
[run\_tests.py]: ../run_tests.py
[test\_libcxx.sh]: ../test_libcxx.py
[validate.py]: ../validate.py
