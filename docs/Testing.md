Testing the NDK
===============

The latest version of this document is available at
https://android.googlesource.com/platform/ndk/+/master/docs/Testing.md.

The NDK tests are built as part of a normal build (with `checkbuild.py`) and run
with `run_tests.py`. (See [README.md] for more instructions on building the
NDK).

From the NDK source directory (`./ndk` within the directory you ran `repo init`
in, or the root of the cloned directory if you cloned only the NDK project).

```bash
$ ./checkbuild.py  # Build the NDK and tests.
$ ./run_tests.py
```

Running the tests requires `adb` in your path and compatible devices attached.
Note that the version of `adb` in the SDK manager might be surprisingly old.
If you're having trouble with the version from the SDK manager, try a version
built fresh from AOSP.

The test runner will look for any attached devices that match the
requirements listed in the `devices` section of the test configuration file (see
[qa\_config.yaml] for the defaults, or use `--config` to choose your own). Each
test will be run on all devices compatible with that test.

The full QA configuration takes roughly 20 minutes to run (Z840 Linux host,
Galaxy Nexi for ICS and Jelly Bean, and Pixel for Nougat).

The tests can be rebuilt without running `checkbuild.py` (which is necessary in
the case of not having a full NDK checkout, as you might when running the
Windows tests on a release from the build server) with `run_tests.py --rebuild`.

[qa\_config.yaml]: ../qa_config.yaml
[README.md]: ../README.md


Restricting Test Configurations
-------------------------------

By default, all of the configurations we test are built from both
`checkbuild.py` and `run_tests.py --rebuild`. This runs several tens of
thousands of test executables (each test is built in 84 different configurations
at time of writing). The set of configurations built can be restricted in two
ways.

First, `run_tests.py --config myconfig.yaml` will use an alternate test
configuration file (the default is `qa_config.yaml`).

Second, and simpler for a development workflow, the following flags can be used
to restrict the configurations (the presence of any of these flags will override
the matching entry in the config file, but otherwise the config file is obeyed):

```bash
$ ./run_tests.py --rebuild \
    --abi armeabi-v7a \
    --toolchain clang \
    --headers unified \
    --pie true
```

All of the flags are repeatable. For example, `--abi armeabi-v7a --abi x86` will
build both armeabi-v7a and x86 tests.

Beyond restricting test configurations, the tests themselves can be filtered
with the `--filter` flag:

```bash
$ ./run_tests.py --filter test-googletest-full
```

Test filters support wildcards (as implemented by Python's `fnmatch.fnmatch`).
The filter flag may be combined with the build configuration flags.

Putting this all together, a single test can be rebuilt and run for just
armeabi-v7a, using only Clang, only unified headers, and only PIE executables
with the following command:

```bash
$ ./run_tests.py --rebuild \
    --abi armeabi-v7a \
    --toolchain clang \
    --headers unified \
    --pie true \
    --filter test-googletest-full
```


Testing Releases
----------------

When testing a release candidate, your first choice should be to run the test
artifacts built on the build server for the given build. This is the
ndk-tests.tar.bz2 artifact in the same directory as the NDK tarball. Extract the
tests somewhere, and then run:

```bash
$ ./run_tests.py path/to/extracted/tests
```

For Windows, test artifacts are not available since we cross compile the NDK
from Linux rather than building on Windows. We want to make sure the Windows
binaries we build work *on* Windows (using wine would only tell us that they
work on wine, which may not be bug compatible with Windows), so those must be
built on the test machine before they can be run. To use the fetched NDK to
build the tests, run:

```bash
$ ./run_tests.py --rebuild --ndk path/to/extracted/ndk out
```


Broken and Unsupported Tests
----------------------------

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

def run_unsupported(abi, device_api, toolchain, name):
    if device_api < 21:
        return device_api
    return None
```

The `*_broken` checks return a tuple of `(broken_configuration, bug_url)` if the
given configuration is known to be broken, else `(None, None)`.

The `*_unsupported` checks return `broken_configuration` if the given
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
* `name`: This is the name of the test executable being run for any of our
  tests. For libc++ tests built by LIT, the executable will be
  `foo.pass.cpp.exe`, but `name` will be `foo.pass`.


Devices and Emulators
---------------------

For testing a release, make sure you're testing against the released builds of
Android.

For Nexus/Pixel devices, factory images are available here:
https://developers.google.com/android/nexus/images. Googlers, you may want to
use the flash station to get a userdebug image since that is needed for ASAN
testing. You should still make sure you also test on user builds because that is
what all of our users have.

For emulators, use emulator images from the SDK rather than from a platform
build. Again, these are what our users will be using. Note that the emulators
are rather unreliable for a number of tests (namely test-googletest-full and
asan-smoke).

After installing the emulator images from the SDK manager, they can be
configured and launched for testing with (assuming the SDK tools directory is in
your path):

```bash
$ android create avd --name $NAME --target android-$LEVEL --abi $ABI
$ emulator -avd $NAME -no-window -writeable-system
```

This will create a new virtual device and launch it in a headless state. Note
that SIGINT will not stop the emulator, and SIGTERM might leave it in a broken
state. To shut down an emulator, use `adb shell reboot -p`.

Note that `-writable-system` is only necessary for running the ASAN tests.

Note that there are no ARM64 emulators whatsoever in the SDK manager. Testing
ARM64 will require a physical device.
