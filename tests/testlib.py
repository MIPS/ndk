#
# Copyright (C) 2015 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import absolute_import
from __future__ import print_function

import distutils.spawn
import imp
import logging
import multiprocessing
import os
import posixpath
import re
import shutil
import subprocess
import time
import traceback
import xml.etree.ElementTree

import build.lib.build_support
import ndk.abis
import ndk.workqueue as wq
import tests.ndk as ndkbuild
import tests.util as util

# pylint: disable=no-self-use


ALL_SUITES = (
    'build',
    'device',
    'libc++',
)


def logger():
    """Return the logger for this module."""
    return logging.getLogger(__name__)


def _get_jobs_arg():
    return '-j{}'.format(multiprocessing.cpu_count() * 2)


def _make_subtest_name(test, case):
    return '.'.join([test, case])


class TestScanner(object):
    """Creates a Test objects for a given test directory.

    A test scanner is used to turn a test directory into a list of Tests for
    any of the test types found in the directory.
    """
    def find_tests(self, path, name):
        """Searches a directory for tests.

        Args:
            path: Path to the test directory.
            name: Name of the test.

        Returns: List of Tests, possibly empty.
        """
        raise NotImplementedError


class BuildConfiguration(object):
    def __init__(self, abi, api, toolchain, force_pie, verbose,
                 force_deprecated_headers):
        self.abi = abi
        self.api = api
        self.toolchain = toolchain
        self.force_pie = force_pie
        self.verbose = verbose
        self.force_deprecated_headers = force_deprecated_headers

    def __eq__(self, other):
        if self.abi != other.abi:
            return False
        if self.api != other.api:
            return False
        if self.toolchain != other.toolchain:
            return False
        if self.force_pie != other.force_pie:
            return False
        if self.verbose != other.verbose:
            return False
        if self.force_deprecated_headers != other.force_deprecated_headers:
            return False
        return True

    def __str__(self):
        pie_option = 'default-pie'
        if self.force_pie:
            pie_option = 'force-pie'

        headers_option = 'unified-headers'
        if self.force_deprecated_headers:
            headers_option = 'deprecated-headers'

        return '{}-{}-{}-{}-{}'.format(
            self.abi, self.api, self.toolchain, pie_option, headers_option)

    def get_extra_ndk_build_flags(self):
        extra_flags = []
        if self.force_pie:
            extra_flags.append('APP_PIE=true')
        if self.verbose:
            extra_flags.append('V=1')
        if self.force_deprecated_headers:
            extra_flags.append('APP_DEPRECATED_HEADERS=true')
        return extra_flags

    def get_extra_cmake_flags(self):
        extra_flags = []
        if self.force_pie:
            extra_flags.append('-DANDROID_PIE=TRUE')
        if self.verbose:
            extra_flags.append('-DCMAKE_VERBOSE_MAKEFILE=ON')
        if self.force_deprecated_headers:
            extra_flags.append('-DANDROID_DEPRECATED_HEADERS=ON')
        return extra_flags


class DeviceConfiguration(BuildConfiguration):
    def __init__(self, abi, api, toolchain, force_pie, verbose,
                 force_deprecated_headers, device, device_api, skip_run):
        super(DeviceConfiguration, self).__init__(
            abi, api, toolchain, force_pie, verbose, force_deprecated_headers)
        self.device = device
        self.device_api = device_api
        self.skip_run = skip_run

    def __eq__(self, other):
        if not super(DeviceConfiguration, self).__eq__(other):
            return False
        if self.device != other.device:
            return False
        if self.device_api != other.device_api:
            return False
        if self.skip_run != other.skip_run:
            return False
        return True


class BuildTestScanner(TestScanner):
    def __init__(self):
        self.build_configurations = set()

    def add_build_configuration(self, abi, api, toolchain, force_pie, verbose,
                                force_deprecated_headers):
        self.build_configurations.add(BuildConfiguration(
            abi, api, toolchain, force_pie, verbose, force_deprecated_headers))

    def find_tests(self, path, name):
        # If we have a build.sh, that takes precedence over the Android.mk.
        build_sh_path = os.path.join(path, 'build.sh')
        if os.path.exists(build_sh_path):
            return self.make_build_sh_tests(path, name)

        # Same for test.py
        build_sh_path = os.path.join(path, 'test.py')
        if os.path.exists(build_sh_path):
            return self.make_test_py_tests(path, name)

        # But we can have both ndk-build and cmake tests in the same directory.
        tests = []
        android_mk_path = os.path.join(path, 'jni/Android.mk')
        if os.path.exists(android_mk_path):
            tests.extend(self.make_ndk_build_tests(path, name))

        cmake_lists_path = os.path.join(path, 'CMakeLists.txt')
        if os.path.exists(cmake_lists_path):
            tests.extend(self.make_cmake_tests(path, name))
        return tests

    def make_build_sh_tests(self, path, name):
        tests = []
        for config in self.build_configurations:
            tests.append(ShellBuildTest(name, path, config))
        return tests

    def make_test_py_tests(self, path, name):
        tests = []
        for config in self.build_configurations:
            tests.append(PythonBuildTest(name, path, config))
        return tests

    def make_ndk_build_tests(self, path, name):
        tests = []
        for config in self.build_configurations:
            tests.append(NdkBuildTest(name, path, config))
        return tests

    def make_cmake_tests(self, path, name):
        tests = []
        for config in self.build_configurations:
            tests.append(CMakeBuildTest(name, path, config))
        return tests


class DeviceTestScanner(TestScanner):
    def __init__(self):
        self.device_configurations = set()

    def add_device_configuration(self, abi, api, toolchain, force_pie, verbose,
                                 force_deprecated_headers, device, device_api,
                                 skip_run):
        self.device_configurations.add(DeviceConfiguration(
            abi, api, toolchain, force_pie, verbose, force_deprecated_headers,
            device, device_api, skip_run))

    def find_tests(self, path, name):
        # If we have a build.sh, that takes precedence over the Android.mk.
        tests = []
        android_mk_path = os.path.join(path, 'jni/Android.mk')
        if os.path.exists(android_mk_path):
            tests.extend(self.make_ndk_build_tests(path, name))

        cmake_lists_path = os.path.join(path, 'CMakeLists.txt')
        if os.path.exists(cmake_lists_path):
            tests.extend(self.make_cmake_tests(path, name))
        return tests

    def make_ndk_build_tests(self, path, name):
        tests = []
        for config in self.device_configurations:
            tests.append(NdkBuildDeviceTest(name, path, config))
        return tests

    def make_cmake_tests(self, path, name):
        tests = []
        for config in self.device_configurations:
            tests.append(CMakeDeviceTest(name, path, config))
        return tests


class LibcxxTestScanner(TestScanner):
    def __init__(self):
        self.device_configurations = set()

    def add_device_configuration(self, abi, api, toolchain, force_pie,
                                 verbose, force_unified_headers, device,
                                 device_api, skip_run):
        self.device_configurations.add(DeviceConfiguration(
            abi, api, toolchain, force_pie, verbose, force_unified_headers,
            device, device_api, skip_run))

    def find_tests(self, path, name):
        tests = []
        for config in self.device_configurations:
            tests.append(LibcxxTest(
                name, path, config.abi, config.api, config.toolchain,
                config.force_unified_headers, config.device, config.device_api,
                config.skip_run))
        return tests


def _scan_test_suite(suite_dir, test_scanner):
    tests = []
    for dentry in os.listdir(suite_dir):
        path = os.path.join(suite_dir, dentry)
        if os.path.isdir(path):
            test_name = os.path.basename(path)
            tests.extend(test_scanner.find_tests(path, test_name))
    return tests


def _fixup_expected_failure(result, config, bug):
    if isinstance(result, Failure):
        return ExpectedFailure(result.test_name, config, bug)
    elif isinstance(result, Success):
        return UnexpectedSuccess(result.test_name, config, bug)
    else:  # Skipped, UnexpectedSuccess, or ExpectedFailure.
        return result


def _fixup_negative_test(result):
    if isinstance(result, Failure):
        return Success(result.test_name)
    elif isinstance(result, Success):
        return Failure(result.test_name, 'negative test case succeeded')
    else:  # Skipped, UnexpectedSuccess, or ExpectedFailure.
        return result


def _run_test(suite, test, out_dir, test_filters):
    """Runs a given test according to the given filters.

    Args:
        suite: Name of the test suite the test belongs to.
        test: The test to be run.
        out_dir: Out directory for building tests.
        test_filters: Filters to apply when running tests.

    Returns: Tuple of (suite, TestResult, [Test]). The [Test] element is a list
             of additional tests to be run.
    """
    if not test_filters.filter(test.name):
        return suite, None, []

    config = test.check_unsupported()
    if config is not None:
        message = 'test unsupported for {}'.format(config)
        return suite, Skipped(test.name, message), []

    try:
        result, additional_tests = test.run(out_dir, test_filters)
        if test.is_negative_test():
            result = _fixup_negative_test(result)
        config, bug = test.check_broken()
        if config is not None:
            # We need to check change each pass/fail to either an
            # ExpectedFailure or an UnexpectedSuccess as necessary.
            result = _fixup_expected_failure(result, config, bug)
    except Exception:  # pylint: disable=broad-except
        result = Failure(test.name, traceback.format_exc())
        additional_tests = []
    return suite, result, additional_tests


class TestRunner(object):
    def __init__(self, printer):
        self.printer = printer
        self.tests = {}

    def add_suite(self, name, path, test_scanner):
        if name in self.tests:
            raise KeyError('suite {} already exists'.format(name))
        self.tests[name] = _scan_test_suite(path, test_scanner)

    def run(self, out_dir, test_filters):
        workqueue = wq.WorkQueue()
        try:
            for suite, tests in self.tests.items():
                for test in tests:
                    workqueue.add_task(
                        _run_test, suite, test, out_dir, test_filters)

            results = {suite: [] for suite in self.tests.keys()}
            while not workqueue.finished():
                suite, result, additional_tests = workqueue.get_result()
                for test in additional_tests:
                    workqueue.add_task(
                        _run_test, suite, test, out_dir, test_filters)
                # Filtered test. Skip them entirely to avoid polluting
                # --show-all results.
                if result is None:
                    continue
                results[suite].append(result)
                self.printer.print_result(result)
            return results
        finally:
            workqueue.terminate()
            workqueue.join()


class TestResult(object):
    def __init__(self, test_name):
        self.test_name = test_name

    def __repr__(self):
        return self.to_string(colored=False)

    def passed(self):
        raise NotImplementedError

    def failed(self):
        raise NotImplementedError

    def to_string(self, colored=False):
        raise NotImplementedError


class Failure(TestResult):
    def __init__(self, test_name, message):
        super(Failure, self).__init__(test_name)
        self.message = message

    def passed(self):
        return False

    def failed(self):
        return True

    def to_string(self, colored=False):
        label = util.maybe_color('FAIL', 'red', colored)
        return '{} {}: {}'.format(label, self.test_name, self.message)


class Success(TestResult):
    def passed(self):
        return True

    def failed(self):
        return False

    def to_string(self, colored=False):
        label = util.maybe_color('PASS', 'green', colored)
        return '{} {}'.format(label, self.test_name)


class Skipped(TestResult):
    def __init__(self, test_name, reason):
        super(Skipped, self).__init__(test_name)
        self.reason = reason

    def passed(self):
        return False

    def failed(self):
        return False

    def to_string(self, colored=False):
        label = util.maybe_color('SKIP', 'yellow', colored)
        return '{} {}: {}'.format(label, self.test_name, self.reason)


class ExpectedFailure(TestResult):
    def __init__(self, test_name, config, bug):
        super(ExpectedFailure, self).__init__(test_name)
        self.config = config
        self.bug = bug

    def passed(self):
        return True

    def failed(self):
        return False

    def to_string(self, colored=False):
        label = util.maybe_color('KNOWN FAIL', 'yellow', colored)
        return '{} {}: known failure for {} ({})'.format(
            label, self.test_name, self.config, self.bug)


class UnexpectedSuccess(TestResult):
    def __init__(self, test_name, config, bug):
        super(UnexpectedSuccess, self).__init__(test_name)
        self.config = config
        self.bug = bug

    def passed(self):
        return False

    def failed(self):
        return True

    def to_string(self, colored=False):
        label = util.maybe_color('SHOULD FAIL', 'red', colored)
        return '{} {}: unexpected success for {} ({})'.format(
            label, self.test_name, self.config, self.bug)


class Test(object):
    def __init__(self, name, test_dir):
        self.name = name
        self.test_dir = test_dir

    def get_test_config(self):
        return TestConfig.from_test_dir(self.test_dir)

    def run(self, out_dir, test_filters):
        raise NotImplementedError


def _prep_build_dir(src_dir, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(src_dir, out_dir)


class TestConfig(object):
    """Describes the status of a test.

    Each test directory can contain a "test_config.py" file that describes
    the configurations a test is not expected to pass for. Previously this
    information could be captured in one of two places: the Application.mk
    file, or a BROKEN_BUILD/BROKEN_RUN file.

    Application.mk was used to state that a test was only to be run for a
    specific platform version, specific toolchain, or a set of ABIs.
    Unfortunately Application.mk could only specify a single toolchain or
    platform, not a set.

    BROKEN_BUILD/BROKEN_RUN files were too general. An empty file meant the
    test should always be skipped regardless of configuration. Any change that
    would put a test in that situation should be reverted immediately. These
    also didn't make it clear if the test was actually broken (and thus should
    be fixed) or just not applicable.

    A test_config.py file is more flexible. It is a Python module that defines
    at least one function by the same name as one in TestConfig.NullTestConfig.
    If a function is not defined the null implementation (not broken,
    supported), will be used.
    """

    class NullTestConfig(object):
        def __init__(self):
            pass

        # pylint: disable=unused-argument
        @staticmethod
        def build_broken(abi, platform, toolchain):
            """Tests if a given configuration is known broken.

            A broken test is a known failing test that should be fixed.

            Any test with a non-empty broken section requires a "bug" entry
            with a link to either an internal bug (http://b/BUG_NUMBER) or a
            public bug (http://b.android.com/BUG_NUMBER).

            These tests will still be built and run. If the test succeeds, it
            will be reported as an error.

            Returns: A tuple of (broken_configuration, bug) or (None, None).
            """
            return None, None

        @staticmethod
        def build_unsupported(abi, platform, toolchain):
            """Tests if a given configuration is unsupported.

            An unsupported test is a test that do not make sense to run for a
            given configuration. Testing x86 assembler on MIPS, for example.

            These tests will not be built or run.

            Returns: The string unsupported_configuration or None.
            """
            return None

        @staticmethod
        def extra_cmake_flags():
            return []

        @staticmethod
        def extra_ndk_build_flags():
            """Returns extra flags that should be passed to ndk-build."""
            return []

        @staticmethod
        def is_negative_test():
            """Returns True if this test should pass if the build fails.

            Note that this is different from build_broken. Use build_broken to
            indicate a bug and use is_negative_test to indicate a test that
            should fail if things are working.

            Also note that check_broken and is_negative_test can be layered. If
            a build is expected to fail, but doesn't for armeabi, the
            test_config could contain:

                def is_negative_test():
                    return True


                def build_broken(abi, api, toolchain):
                    if abi == 'armeabi':
                        return abi, bug_url
                    return None, None
            """
            return False
        # pylint: enable=unused-argument

    def __init__(self, file_path):
        # Note that this namespace isn't actually meaningful from our side;
        # it's only what the loaded module's __name__ gets set to.
        dirname = os.path.dirname(file_path)
        namespace = '.'.join([dirname, 'test_config'])

        try:
            self.module = imp.load_source(namespace, file_path)
        except IOError:
            self.module = None

        try:
            self.build_broken = self.module.build_broken
        except AttributeError:
            self.build_broken = self.NullTestConfig.build_broken

        try:
            self.build_unsupported = self.module.build_unsupported
        except AttributeError:
            self.build_unsupported = self.NullTestConfig.build_unsupported

        try:
            self.extra_cmake_flags = self.module.extra_cmake_flags
        except AttributeError:
            self.extra_cmake_flags = self.NullTestConfig.extra_cmake_flags

        try:
            self.extra_ndk_build_flags = self.module.extra_ndk_build_flags
        except AttributeError:
            ntc = self.NullTestConfig
            self.extra_ndk_build_flags = ntc.extra_ndk_build_flags

        try:
            self.is_negative_test = self.module.is_negative_test
        except AttributeError:
            self.is_negative_test = self.NullTestConfig.is_negative_test

    @classmethod
    def from_test_dir(cls, test_dir):
        path = os.path.join(test_dir, 'test_config.py')
        return cls(path)


class DeviceTestConfig(TestConfig):
    """Specialization of test_config.py that includes device API level.

    We need to mark some tests as broken or unsupported based on what device
    they are running on, as opposed to just what they were built for.
    """
    class NullTestConfig(TestConfig.NullTestConfig):
        # pylint: disable=unused-argument
        @staticmethod
        def run_broken(abi, device_api, toolchain, subtest):
            return None, None

        @staticmethod
        def run_unsupported(abi, device_api, toolchain, subtest):
            return None

        @staticmethod
        def extra_cmake_flags():
            return []
        # pylint: enable=unused-argument

    def __init__(self, file_path):
        super(DeviceTestConfig, self).__init__(file_path)

        try:
            self.run_broken = self.module.run_broken
        except AttributeError:
            self.run_broken = self.NullTestConfig.run_broken

        try:
            self.run_unsupported = self.module.run_unsupported
        except AttributeError:
            self.run_unsupported = self.NullTestConfig.run_unsupported

        try:
            _ = self.module.is_negative_test
            # If the build is expected to fail, then it should just be a build
            # test since the test should never be run.
            #
            # If the run is expected to fail, just fix the test to pass for
            # thatr case. Gtest death tests can handle the more complicated
            # cases.
            raise RuntimeError('is_negative_test is invalid for device tests')
        except AttributeError:
            pass


def _run_build_sh_test(test_name, build_dir, test_dir, ndk_build_flags, abi,
                       platform, toolchain):
    _prep_build_dir(test_dir, build_dir)
    with util.cd(build_dir):
        build_cmd = ['bash', 'build.sh', _get_jobs_arg()] + ndk_build_flags
        test_env = dict(os.environ)
        if abi is not None:
            test_env['APP_ABI'] = abi
        test_env['APP_PLATFORM'] = 'android-{}'.format(platform)
        assert toolchain is not None
        test_env['NDK_TOOLCHAIN_VERSION'] = toolchain
        rc, out = util.call_output(build_cmd, env=test_env)
        if rc == 0:
            return Success(test_name)
        else:
            return Failure(test_name, out)


def _run_ndk_build_test(test_name, build_dir, test_dir, ndk_build_flags, abi,
                        platform, toolchain):
    _prep_build_dir(test_dir, build_dir)
    with util.cd(build_dir):
        args = [
            'APP_ABI=' + abi,
            'NDK_TOOLCHAIN_VERSION=' + toolchain,
            _get_jobs_arg(),
        ]
        if platform is not None:
            args.append('APP_PLATFORM=android-{}'.format(platform))
        rc, out = ndkbuild.build(args + ndk_build_flags)
        if rc == 0:
            return Success(test_name)
        else:
            return Failure(test_name, out)


def _run_cmake_build_test(test_name, build_dir, test_dir, cmake_flags, abi,
                          platform, toolchain):
    _prep_build_dir(test_dir, build_dir)

    # Add prebuilts to PATH.
    prebuilts_host_tag = build.lib.build_support.get_default_host() + '-x86'
    prebuilts_bin = build.lib.build_support.android_path(
        'prebuilts', 'cmake', prebuilts_host_tag, 'bin')
    env = dict(os.environ)
    env['PATH'] = prebuilts_bin + os.pathsep + os.environ['PATH']

    # Skip if we don't have a working cmake executable, either from the
    # prebuilts, or from the SDK, or if a new enough version is installed.
    if distutils.spawn.find_executable('cmake') is None:
        return Skipped(test_name, 'cmake executable not found')
    out = subprocess.check_output(['cmake', '--version'], env=env)
    version_pattern = r'cmake version (\d+)\.(\d+)\.'
    version = [int(v) for v in re.match(version_pattern, out).groups()]
    if version < [3, 6]:
        return Skipped(test_name, 'cmake 3.6 or above required')

    toolchain_file = os.path.join(os.environ['NDK'], 'build', 'cmake',
                                  'android.toolchain.cmake')
    objs_dir = os.path.join(build_dir, 'objs', abi)
    libs_dir = os.path.join(build_dir, 'libs', abi)
    if toolchain != 'clang':
        toolchain = 'gcc'
    args = [
        '-H' + build_dir,
        '-B' + objs_dir,
        '-DCMAKE_TOOLCHAIN_FILE=' + toolchain_file,
        '-DANDROID_ABI=' + abi,
        '-DANDROID_TOOLCHAIN=' + toolchain,
        '-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=' + libs_dir,
        '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + libs_dir
    ]
    rc, _ = util.call_output(['ninja', '--version'], env=env)
    if rc == 0:
        args += [
            '-GNinja',
            '-DCMAKE_MAKE_PROGRAM=ninja',
        ]
    if platform is not None:
        args.append('-DANDROID_PLATFORM=android-{}'.format(platform))
    rc, out = util.call_output(['cmake'] + cmake_flags + args, env=env)
    if rc != 0:
        return Failure(test_name, out)
    rc, out = util.call_output(['cmake', '--build', objs_dir,
                                '--', _get_jobs_arg()], env=env)
    if rc != 0:
        return Failure(test_name, out)
    return Success(test_name)


class BuildTest(Test):
    def __init__(self, name, test_dir, config):
        super(BuildTest, self).__init__(name, test_dir)

        self.config = config

        if self.api is None:
            raise ValueError

    @property
    def abi(self):
        return self.config.abi

    @property
    def api(self):
        return self.config.api

    @property
    def platform(self):
        return self.api

    @property
    def toolchain(self):
        return self.config.toolchain

    @property
    def ndk_build_flags(self):
        flags = self.config.get_extra_ndk_build_flags()
        if flags is None:
            flags = []
        return flags + self.get_extra_ndk_build_flags()

    @property
    def cmake_flags(self):
        flags = self.config.get_extra_cmake_flags()
        if flags is None:
            flags = []
        return flags + self.get_extra_cmake_flags()

    def run(self, out_dir, _):
        raise NotImplementedError

    def check_broken(self):
        return self.get_test_config().build_broken(
            self.abi, self.platform, self.toolchain)

    def check_unsupported(self):
        return self.get_test_config().build_unsupported(
            self.abi, self.platform, self.toolchain)

    def is_negative_test(self):
        return self.get_test_config().is_negative_test()

    def get_extra_cmake_flags(self):
        return self.get_test_config().extra_cmake_flags()

    def get_extra_ndk_build_flags(self):
        return self.get_test_config().extra_ndk_build_flags()


class PythonBuildTest(BuildTest):
    """A test that is implemented by test.py.

    A test.py test has a test.py file in its root directory. This module
    contains a run_test function which returns a tuple of `(boolean_success,
    string_failure_message)` and takes the following kwargs (all of which
    default to None):

    abi: ABI to test as a string.
    platform: Platform to build against as a string.
    toolchain: Toolchain to use as a string.
    ndk_build_flags: Additional build flags that should be passed to ndk-build
                     if invoked as a list of strings.
    """
    def __init__(self, name, test_dir, config):
        api = config.api
        if api is None:
            api = build.lib.build_support.minimum_platform_level(config.abi)
        config = BuildConfiguration(
            config.abi, api, config.toolchain, config.force_pie,
            config.verbose, config.force_deprecated_headers)
        super(PythonBuildTest, self).__init__(name, test_dir, config)

    def get_build_dir(self, out_dir):
        return os.path.join(
            out_dir, 'build/test.py', str(self.config), self.name)

    def run(self, out_dir, _):
        build_dir = self.get_build_dir(out_dir)
        print('Building test: {}'.format(self.name))
        _prep_build_dir(self.test_dir, build_dir)
        with util.cd(build_dir):
            module = imp.load_source('test', 'test.py')
            success, failure_message = module.run_test(
                abi=self.abi, platform=self.platform, toolchain=self.toolchain,
                build_flags=self.ndk_build_flags)
            if success:
                return Success(self.name), []
            else:
                return Failure(self.name, failure_message), []


class ShellBuildTest(BuildTest):
    def __init__(self, name, test_dir, config):
        api = config.api
        if api is None:
            api = build.lib.build_support.minimum_platform_level(config.abi)
        config = BuildConfiguration(
            config.abi, api, config.toolchain, config.force_pie,
            config.verbose, config.force_deprecated_headers)
        super(ShellBuildTest, self).__init__(name, test_dir, config)

    def get_build_dir(self, out_dir):
        return os.path.join(
            out_dir, 'build/build.sh', str(self.config), self.name)

    def run(self, out_dir, _):
        build_dir = self.get_build_dir(out_dir)
        print('Building test: {}'.format(self.name))
        if os.name == 'nt':
            reason = 'build.sh tests are not supported on Windows'
            return Skipped(self.name, reason), []
        else:
            result = _run_build_sh_test(
                self.name, build_dir, self.test_dir, self.ndk_build_flags,
                self.abi, self.platform, self.toolchain)
            return result, []


def _platform_from_application_mk(test_dir):
    """Determine target API level from a test's Application.mk.

    Args:
        test_dir: Directory of the test to read.

    Returns:
        Integer portion of APP_PLATFORM if found, else None.

    Raises:
        ValueError: Found an unexpected value for APP_PLATFORM.
    """
    application_mk = os.path.join(test_dir, 'jni/Application.mk')
    if not os.path.exists(application_mk):
        return None

    with open(application_mk) as application_mk_file:
        for line in application_mk_file:
            if line.startswith('APP_PLATFORM'):
                _, platform_str = line.split(':=')
                break
        else:
            return None

    platform_str = platform_str.strip()
    if not platform_str.startswith('android-'):
        raise ValueError(platform_str)

    _, api_level_str = platform_str.split('-')
    return int(api_level_str)


def _get_or_infer_app_platform(platform_from_user, test_dir, abi):
    """Determines the platform level to use for a test using ndk-build.

    Choose the platform level from, in order of preference:
    1. Value given as argument.
    2. APP_PLATFORM from jni/Application.mk.
    3. Default value for the target ABI.

    Args:
        platform_from_user: A user provided platform level or None.
        test_dir: The directory containing the ndk-build project.
        abi: The ABI being targeted.

    Returns:
        The platform version the test should build against.
    """
    if platform_from_user is not None:
        return platform_from_user

    platform_from_application_mk = _platform_from_application_mk(test_dir)
    if platform_from_application_mk is not None:
        return platform_from_application_mk

    return build.lib.build_support.minimum_platform_level(abi)


class NdkBuildTest(BuildTest):
    def __init__(self, name, test_dir, config):
        api = _get_or_infer_app_platform(config.api, test_dir, config.abi)
        config = BuildConfiguration(
            config.abi, api, config.toolchain, config.force_pie,
            config.verbose, config.force_deprecated_headers)
        super(NdkBuildTest, self).__init__(name, test_dir, config)

    def get_build_dir(self, out_dir):
        return os.path.join(
            out_dir, 'build/ndk-build', str(self.config), self.name)

    def run(self, out_dir, _):
        build_dir = self.get_build_dir(out_dir)
        print('Building test: {}'.format(self.name))
        result = _run_ndk_build_test(
            self.name, build_dir, self.test_dir, self.ndk_build_flags,
            self.abi, self.platform, self.toolchain)
        return result, []


class CMakeBuildTest(BuildTest):
    def __init__(self, name, test_dir, config):
        api = _get_or_infer_app_platform(config.api, test_dir, config.abi)
        config = BuildConfiguration(
            config.abi, api, config.toolchain, config.force_pie,
            config.verbose, config.force_deprecated_headers)
        super(CMakeBuildTest, self).__init__(name, test_dir, config)

    def get_build_dir(self, out_dir):
        return os.path.join(
            out_dir, 'build/cmake', str(self.config), self.name)

    def run(self, out_dir, _):
        build_dir = self.get_build_dir(out_dir)
        print('Building test: {}'.format(self.name))
        result = _run_cmake_build_test(
            self.name, build_dir, self.test_dir, self.cmake_flags, self.abi,
            self.platform, self.toolchain)
        return result, []


def is_text_busy(out):
    # Anything longer than this isn't going to be a text busy message, so don't
    # waste time scanning it.
    if len(out) > 1024:
        return False
    # 'text busy' was printed on Gingerbread.
    if 'text busy' in out:
        return True
    # 'Text file busy' was printed on Jelly Bean (not sure exactly when this
    # changed).
    if 'Text file busy' in out:
        return True
    return False


class DeviceTest(Test):
    def __init__(self, name, test_dir, config):
        super(DeviceTest, self).__init__(name, test_dir)

        api = _get_or_infer_app_platform(config.api, test_dir, config.abi)
        config = DeviceConfiguration(
            config.abi, api, config.toolchain, config.force_pie,
            config.verbose, config.force_deprecated_headers, config.device,
            config.device_api, config.skip_run)
        self.config = config

    @property
    def abi(self):
        return self.config.abi

    @property
    def api(self):
        return self.config.api

    @property
    def platform(self):
        return self.api

    @property
    def toolchain(self):
        return self.config.toolchain

    @property
    def device(self):
        return self.config.device

    @property
    def device_api(self):
        return self.config.device_api

    @property
    def skip_run(self):
        return self.config.skip_run

    def check_broken(self):
        return self.get_test_config().build_broken(
            self.abi, self.platform, self.toolchain)

    def check_unsupported(self):
        return self.get_test_config().build_unsupported(
            self.abi, self.platform, self.toolchain)

    def is_negative_test(self):
        return False

    def run(self, out_dir, test_filters):
        raise NotImplementedError

    def get_device_subdir(self):
        raise NotImplementedError

    def get_device_dir(self):
        return posixpath.join(
            '/data/local/tmp', self.get_device_subdir(), self.name)

    def copy_test_to_device(self, build_dir, test_filters):
        self.device.shell_nocheck(['rm -r {}'.format(self.get_device_dir())])

        abi_dir = os.path.join(build_dir, 'libs', self.abi)
        if not os.path.isdir(abi_dir):
            raise RuntimeError('No libraries for {}'.format(self.abi))

        print('Pushing {} to {}...'.format(abi_dir, self.get_device_dir()))
        self.device.push(abi_dir, self.get_device_dir())
        for test_file in os.listdir(abi_dir):
            if test_file in ('gdbserver', 'gdb.setup'):
                continue

            file_is_lib = True
            if not test_file.endswith('.so'):
                file_is_lib = False
                case_name = _make_subtest_name(self.name, test_file)
                if not test_filters.filter(case_name):
                    continue

            # Binaries pushed from Windows may not have execute permissions.
            if not file_is_lib:
                file_path = posixpath.join(self.get_device_dir(), test_file)
                # Can't use +x because apparently old versions of Android
                # didn't support that...
                self.device.shell(['chmod', '777', file_path])

    def get_test_executables(self, build_dir, test_filters):
        abi_dir = os.path.join(build_dir, 'libs', self.abi)
        if not os.path.isdir(abi_dir):
            raise RuntimeError('No libraries for {}'.format(self.abi))

        test_cases = []
        for test_file in os.listdir(abi_dir):
            if test_file in ('gdbserver', 'gdb.setup'):
                continue

            if test_file.endswith('.so'):
                continue

            case_name = _make_subtest_name(self.name, test_file)
            if not test_filters.filter(case_name):
                continue
            test_cases.append(test_file)

        if len(test_cases) == 0:
            raise RuntimeError('Could not find any test executables.')

        return test_cases

    def get_additional_tests(self, build_dir, test_filters):
        additional_tests = []
        self.copy_test_to_device(build_dir, test_filters)
        for exe in self.get_test_executables(build_dir, test_filters):
            name = _make_subtest_name(self.name, exe)
            run_test = DeviceRunTest(
                name, self.test_dir, exe, self.get_device_dir(), self.config)
            additional_tests.append(run_test)
        return additional_tests


class NdkBuildDeviceTest(DeviceTest):
    def __init__(self, name, test_dir, config):
        super(NdkBuildDeviceTest, self).__init__(name, test_dir, config)

    def get_extra_ndk_build_flags(self):
        return self.get_test_config().extra_ndk_build_flags()

    @property
    def ndk_build_flags(self):
        flags = self.config.get_extra_ndk_build_flags()
        if flags is None:
            flags = []
        return flags + self.get_extra_ndk_build_flags()

    def get_device_subdir(self):
        return 'ndk-tests'

    def get_build_dir(self, out_dir):
        return os.path.join(
            out_dir, 'device/ndk-build', str(self.config), self.name)

    def run(self, out_dir, test_filters):
        print('Building device test with ndk-build: {}'.format(self.name))
        build_dir = self.get_build_dir(out_dir)
        build_result = _run_ndk_build_test(self.name, build_dir, self.test_dir,
                                           self.ndk_build_flags, self.abi,
                                           self.platform, self.toolchain)
        if not build_result.passed():
            return build_result, []

        if self.skip_run:
            return build_result, []

        return build_result, self.get_additional_tests(build_dir, test_filters)


class CMakeDeviceTest(DeviceTest):
    def __init__(self, name, test_dir, config):
        super(CMakeDeviceTest, self).__init__(name, test_dir, config)

    def get_extra_cmake_flags(self):
        return self.get_test_config().extra_cmake_flags()

    @property
    def cmake_flags(self):
        flags = self.config.get_extra_cmake_flags()
        if flags is None:
            flags = []
        return flags + self.get_extra_cmake_flags()

    def get_device_subdir(self):
        return 'cmake-tests'

    def get_build_dir(self, out_dir):
        return os.path.join(
            out_dir, 'device/cmake', str(self.config), self.name)

    def run(self, out_dir, test_filters):
        print('Building device test with cmake: {}'.format(self.name))
        build_dir = self.get_build_dir(out_dir)
        build_result = _run_cmake_build_test(self.name, build_dir,
                                             self.test_dir, self.cmake_flags,
                                             self.abi, self.platform,
                                             self.toolchain)
        if not build_result.passed():
            return build_result, []

        if self.skip_run:
            return build_result, []

        return build_result, self.get_additional_tests(build_dir, test_filters)


class DeviceRunTest(Test):
    def __init__(self, name, test_dir, case_name, device_dir, config):
        super(DeviceRunTest, self).__init__(name, test_dir)
        self.config = config
        self.case_name = case_name
        self.device_dir = device_dir

    @property
    def abi(self):
        return self.config.abi

    @property
    def build_api(self):
        return self.config.api

    @property
    def toolchain(self):
        return self.config.toolchain

    @property
    def device(self):
        return self.config.device

    @property
    def device_api(self):
        return self.config.device_api

    def get_test_config(self):
        return DeviceTestConfig.from_test_dir(self.test_dir)

    def check_broken(self):
        return self.get_test_config().run_broken(
            self.abi, self.device_api, self.toolchain, self.case_name)

    def check_unsupported(self):
        if self.build_api > self.device_api:
            return 'device platform {} < build platform {}'.format(
                self.device_api, self.build_api)
        return self.get_test_config().run_unsupported(
            self.abi, self.device_api, self.toolchain, self.case_name)

    def is_negative_test(self):
        return False

    def run(self, out_dir, test_filters):
        cmd = 'cd {} && LD_LIBRARY_PATH={} ./{} 2>&1'.format(
            self.device_dir, self.device_dir, self.case_name)
        for _ in range(8):
            result, out, _ = self.device.shell_nocheck([cmd])
            if result == 0:
                break
            if not is_text_busy(out):
                break
            time.sleep(1)

        if result == 0:
            return Success(self.name), []
        else:
            return Failure(self.name, out), []


def get_xunit_reports(xunit_file, abi, api, toolchain, device_api, skip_run):
    tree = xml.etree.ElementTree.parse(xunit_file)
    root = tree.getroot()
    cases = root.findall('.//testcase')

    reports = []
    for test_case in cases:
        test_dir = test_case.get('classname')
        if test_dir.startswith('libc++.'):
            test_dir = test_dir[len('libc++.'):]

        name = '/'.join([test_dir, test_case.get('name')])

        failure_nodes = test_case.findall('failure')
        if len(failure_nodes) == 0:
            reports.append(XunitSuccess(
                name, test_dir, abi, api, toolchain, device_api, skip_run))
            continue

        if len(failure_nodes) != 1:
            msg = ('Could not parse XUnit output: test case does not have a '
                   'unique failure node: {}'.format(name))
            raise RuntimeError(msg)

        failure_node = failure_nodes[0]
        failure_text = failure_node.text
        reports.append(XunitFailure(
            name, test_dir, failure_text, abi, api, toolchain, device_api,
            skip_run))
    return reports


class LibcxxTest(Test):
    def __init__(self, name, test_dir, abi, api, toolchain, unified_headers,
                 device, device_api, skip_run):
        super(LibcxxTest, self).__init__(name, test_dir)

        if api is None:
            api = ndk.abis.min_api_for_abi(abi)

        self.abi = abi
        self.api = api
        self.toolchain = toolchain
        self.unified_headers = unified_headers
        self.device = device
        self.device_api = device_api
        self.skip_run = skip_run

    def run(self, out_dir, test_filters):
        xunit_output = os.path.join(out_dir, 'xunit.xml')
        cmd = [
            'python', '../test_libcxx.py',
            '--abi', self.abi,
            '--platform', str(self.api),

            # We don't want the progress bar since we're already printing our
            # own output, so we need --show-all so we get *some* output,
            # otherwise it would just be quiet for several minutes and it
            # wouldn't be clear if something had hung.
            '--no-progress-bar',
            '--show-all',

            '--xunit-xml-output=' + xunit_output,

            '--timeout=600',
        ]

        if self.unified_headers:
            cmd.append('--unified-headers')

        if self.skip_run:
            cmd.append('--param=build_only=True')

        # Ignore the exit code. We do most XFAIL processing outside the test
        # runner so expected failures in the test runner will still cause a
        # non-zero exit status. This "test" only fails if we encounter a Python
        # exception. Exceptions raised from our code are already caught by the
        # test runner. If that happens in test_libcxx.py or in LIT, the xunit
        # output will not be valid and we'll fail get_xunit_reports and raise
        # an exception anyway.
        subprocess.call(cmd)

        # We create a bunch of fake tests that report the status of each
        # individual test in the xunit report.
        test_reports = get_xunit_reports(
            xunit_output, self.abi, self.api, self.toolchain, self.device_api,
            self.skip_run)

        return Success(self.name), test_reports

    def check_broken(self):
        # Actual results are reported individually by pulling them out of the
        # xunit output. This just reports the status of the overall test run,
        # which should be passing.
        return None, None

    def check_unsupported(self):
        # The NDK's libc++ support has always come with a big scary beta label
        # on it. The tests have never been 100% passing. We're going to only
        # enable it for a handful of configurations as support falls in to
        # place.
        if not self.unified_headers:
            return 'legacy headers'
        if self.toolchain == '4.9':
            return '4.9'
        if self.abi != 'armeabi-v7a':
            # The ABI case is something we will eventually support, but don't
            # bother wasting time running them until we get to that point.
            return self.abi
        return None

    def is_negative_test(self):
        return False


class LibcxxTestConfig(DeviceTestConfig):
    """Specialization of test_config.py for libc++.

    The libc++ tests have multiple tests in a single directory, so we need to
    pass the test name for build_broken too.
    """
    class NullTestConfig(TestConfig.NullTestConfig):
        # pylint: disable=unused-argument,arguments-differ
        @staticmethod
        def build_unsupported(abi, api, toolchain, name):
            return None

        @staticmethod
        def build_broken(abi, api, toolchain, name):
            return None, None

        @staticmethod
        def run_unsupported(abi, device_api, toolchain, name):
            return None

        @staticmethod
        def run_broken(abi, device_api, toolchain, name):
            return None, None
        # pylint: enable=unused-argument,arguments-differ


class XunitResult(Test):
    """Fake tests so we can show a result for each libc++ test.

    We create these by parsing the xunit XML output from the libc++ test
    runner. For each result, we create an XunitResult "test" that simply
    returns a result for the xunit status.

    We don't have an ExpectedFailure form of the XunitResult because that is
    already handled for us by the libc++ test runner.
    """
    def __init__(self, name, test_dir, abi, api, toolchain, device_api,
                 skip_run):
        super(XunitResult, self).__init__(name, test_dir)
        self.abi = abi
        self.api = api
        self.toolchain = toolchain
        self.device_api = device_api
        self.skip_run = skip_run

    def run(self, _out_dir, _test_filters):
        raise NotImplementedError

    def get_test_config(self):
        test_config_dir = build.lib.build_support.ndk_path(
            'tests/libc++/test', self.test_dir)
        return LibcxxTestConfig.from_test_dir(test_config_dir)

    def check_broken(self):
        name = os.path.splitext(os.path.basename(self.name))[0]
        config, bug = self.get_test_config().build_broken(
            self.abi, self.api, self.toolchain, name)
        if config is not None:
            return config, bug

        if not self.skip_run:
            return self.get_test_config().run_broken(
                self.abi, self.device_api, self.toolchain, name)
        return None, None

    def check_unsupported(self):
        return None

    def is_negative_test(self):
        return False


class XunitSuccess(XunitResult):
    def run(self, _out_dir, _test_filters):
        return Success(self.name), []


class XunitFailure(XunitResult):
    def __init__(self, name, test_dir, text, abi, api, toolchain, device_api,
                 skip_run):
        super(XunitFailure, self).__init__(
            name, test_dir, abi, api, toolchain, device_api, skip_run)
        self.text = text

    def run(self, _out_dir, _test_filters):
        return Failure(self.name, self.text), []
