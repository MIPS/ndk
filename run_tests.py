#!/usr/bin/env python
#
# Copyright (C) 2017 The Android Open Source Project
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
"""Runs the tests built by make_tests.py."""
from __future__ import print_function

import argparse
import json
import logging
import os
import posixpath
import random
import site
import subprocess
import sys
import time

import build.lib.build_support
import ndk.paths
import ndk.subprocess
import ndk.test.builder
import ndk.test.devices
import ndk.test.report
import ndk.test.result
import ndk.test.spec
import ndk.workqueue

import tests.filters as filters
import tests.printers as printers
import tests.testlib as testlib


DEVICE_TEST_BASE_DIR = '/data/local/tmp/tests'


def logger():
    """Returns the module logger."""
    return logging.getLogger(__name__)


# TODO: Extract a common interface from this and testlib.Test for the printer.
class TestCase(object):
    """A test case found in the dist directory.

    The test directory is structured as tests/dist/$CONFIG/$BUILD_SYTEM/...
    What follows depends on the type of test case. Each discovered test case
    will have a name, a build configuration, a build system, and a device
    directory.
    """
    def __init__(self, name, config, build_system, device_dir):
        self.name = name
        self.config = config
        self.build_system = build_system
        self.device_dir = device_dir

    def check_unsupported(self, device):
        raise NotImplementedError

    def check_broken(self, device):
        raise NotImplementedError

    def run(self, device):
        raise NotImplementedError


class BasicTestCase(TestCase):
    """A test case for the standard NDK test builder.

    These tests were written specifically for the NDK and thus follow the
    layout we expect. In each test configuration directory, we have
    $TEST_SUITE/$ABI/$TEST_FILES. $TEST_FILES includes both the shared
    libraries for the test and the test executables.
    """
    def __init__(self, suite, executable, config, build_system, device_dir):
        name = '.'.join([suite, executable])
        super(BasicTestCase, self).__init__(
            name, config, build_system, device_dir)

        self.suite = suite
        self.executable = executable

    def get_test_config(self):
        # We don't run anything in tests/build, and the libc++ tests are
        # handled by a different LibcxxTest. We can safely assume that anything
        # here is in tests/device.
        test_dir = build.lib.build_support.ndk_path('tests/device', self.suite)
        return testlib.DeviceTestConfig.from_test_dir(test_dir)

    def check_unsupported(self, device):
        return self.get_test_config().run_unsupported(
            self.config.abi, device.version, self.config.toolchain,
            self.executable)

    def check_broken(self, device):
        return self.get_test_config().run_broken(
            self.config.abi, device.version, self.config.toolchain,
            self.executable)

    def run(self, device):
        # May need this for Windows.
        # # Binaries pushed from Windows may not have execute permissions.
        # if not file_is_lib:
        #     file_path = posixpath.join(self.get_device_dir(), test_file)
        #     # Can't use +x because apparently old versions of Android
        #     # didn't support that...
        #     self.device.shell(['chmod', '777', file_path])
        config = self.check_unsupported(device)
        if config is not None:
            message = 'test unsupported for {}'.format(config)
            return ndk.test.result.Skipped(self, message)

        cmd = 'cd {} && LD_LIBRARY_PATH={} ./{} 2>&1'.format(
            self.device_dir, self.device_dir, self.executable)
        logger().info('%s: shell_nocheck "%s"', device.name, cmd)
        return device.shell_nocheck([cmd])


class LibcxxTestCase(TestCase):
    """A libc++ test case built by LIT.

    LIT's test structure doesn't map cleanly to ours; they have a hierarchical
    test structure. The top level contains a single "libc++" directory. In that
    directory is where shared libraries common to all tests are placed. That
    directory and any under it may contain test executables (always suffixed
    with ".exe") or test data (always suffixed with ".dat").
    """
    def __init__(self, suite, executable, config, device_dir):
        name = posixpath.join(suite, executable)
        super(LibcxxTestCase, self).__init__(
            name, config, 'libc++', device_dir)

        self.suite = suite
        self.executable = executable

    def get_test_config(self):
        _, _, test_subdir = self.suite.partition('/')
        test_dir = build.lib.build_support.ndk_path(
            'tests/libc++/test', test_subdir)
        return testlib.LibcxxTestConfig.from_test_dir(test_dir)

    def check_unsupported(self, device):
        # Executable is foo.pass.cpp.exe, we want foo.pass.
        name = os.path.splitext(os.path.splitext(self.executable)[0])[0]
        config = self.get_test_config().run_unsupported(
            self.config.abi, device.version, self.config.toolchain, name)
        if config is not None:
            return config
        return None

    def check_broken(self, device):
        # Executable is foo.pass.cpp.exe, we want foo.pass.
        name = os.path.splitext(os.path.splitext(self.executable)[0])[0]
        config, bug = self.get_test_config().run_broken(
            self.config.abi, device.version, self.config.toolchain, name)
        if config is not None:
            return config, bug
        return None, None

    def run(self, device):
        # May need this for Windows.
        # # Binaries pushed from Windows may not have execute permissions.
        # if not file_is_lib:
        #     file_path = posixpath.join(self.get_device_dir(), test_file)
        #     # Can't use +x because apparently old versions of Android
        #     # didn't support that...
        #     self.device.shell(['chmod', '777', file_path])
        libcxx_so_dir = posixpath.join(
            DEVICE_TEST_BASE_DIR, str(self.config), 'libcxx/libc++')
        cmd = 'cd {} && LD_LIBRARY_PATH={} ./{} 2>&1'.format(
            self.device_dir, libcxx_so_dir, self.executable)
        logger().info('%s: shell_nocheck "%s"', device.name, cmd)
        return device.shell_nocheck([cmd])


class TestRun(object):
    """A test case mapped to the device it will run on."""
    def __init__(self, test_case, device):
        self.test_case = test_case
        self.device = device

    @property
    def name(self):
        return self.test_case.name

    @property
    def build_system(self):
        return self.test_case.build_system

    @property
    def config(self):
        return self.test_case.config

    def make_result(self, adb_result_tuple):
        status, out, _ = adb_result_tuple
        if status == 0:
            result = ndk.test.result.Success(self)
        else:
            out = '\n'.join([str(self.device), out])
            result = ndk.test.result.Failure(self, out)
        return self.fixup_xfail(result)

    def fixup_xfail(self, result):
        config, bug = self.test_case.check_broken(self.device)
        if config is not None:
            if result.failed():
                return ndk.test.result.ExpectedFailure(self, config, bug)
            elif result.passed():
                return ndk.test.result.UnexpectedSuccess(self, config, bug)
            raise ValueError('Test result must have either failed or passed.')
        return result

    def run(self):
        config = self.test_case.check_unsupported(self.device)
        if config is not None:
            message = 'test unsupported for {}'.format(config)
            return ndk.test.result.Skipped(self, message)
        return self.make_result(self.test_case.run(self.device))


def build_tests(ndk_dir, out_dir, clean, printer, config, test_filter):
    test_options = ndk.test.spec.TestOptions(
       ndk_dir, out_dir, verbose_build=True, skip_run=True,
       test_filter=test_filter, clean=clean)

    test_spec = ndk.test.builder.test_spec_from_config(config)
    builder = ndk.test.builder.TestBuilder(test_spec, test_options, printer)

    return builder.build()


def enumerate_basic_tests(out_dir_base, build_cfg, build_system, test_filter):
    tests = []
    tests_dir = os.path.join(out_dir_base, str(build_cfg), build_system)
    if not os.path.exists(tests_dir):
        return tests

    for test_subdir in os.listdir(tests_dir):
        test_dir = os.path.join(tests_dir, test_subdir)
        out_dir = os.path.join(test_dir, build_cfg.abi)
        test_relpath = os.path.relpath(out_dir, out_dir_base)
        device_dir = posixpath.join(DEVICE_TEST_BASE_DIR, test_relpath)
        for test_file in os.listdir(out_dir):
            if test_file.endswith('.so'):
                continue
            name = '.'.join([test_subdir, test_file])
            if not test_filter.filter(name):
                continue
            tests.append(BasicTestCase(
                test_subdir, test_file, build_cfg, build_system, device_dir))
    return tests


def enumerate_libcxx_tests(out_dir_base, build_cfg, build_system, test_filter):
    tests = []
    tests_dir = os.path.join(out_dir_base, str(build_cfg), build_system)
    if not os.path.exists(tests_dir):
        return tests

    for root, _, files in os.walk(tests_dir):
        for test_file in files:
            if not test_file.endswith('.exe'):
                continue
            test_relpath = os.path.relpath(root, out_dir_base)
            device_dir = posixpath.join(DEVICE_TEST_BASE_DIR, test_relpath)
            suite_name = os.path.relpath(root, tests_dir)
            name = '/'.join([suite_name, test_file])
            if not test_filter.filter(name):
                continue
            tests.append(LibcxxTestCase(
                suite_name, test_file, build_cfg, device_dir))
    return tests


def enumerate_tests(test_dir, test_filter, config_filter):
    tests = {}

    # The tests directory has a directory for each type of test. For example:
    #
    #  * build.sh
    #  * cmake
    #  * libcxx
    #  * ndk-build
    #  * test.py
    #
    # We need to handle some of these differently. The test.py and build.sh
    # type tests are build only, so we don't need to run them. The libc++ tests
    # are built by a test runner we don't control, so its output doesn't quite
    # match what we expect.
    test_subdir_class_map = {
        'cmake': enumerate_basic_tests,
        'libcxx': enumerate_libcxx_tests,
        'ndk-build': enumerate_basic_tests,
    }

    for build_cfg_str in os.listdir(test_dir):
        build_cfg = ndk.test.spec.BuildConfiguration.from_string(build_cfg_str)
        if not config_filter.filter(build_cfg):
            continue

        if build_cfg not in tests:
            tests[build_cfg] = []

        for test_type, scan_for_tests in test_subdir_class_map.items():
            tests[build_cfg].extend(
                scan_for_tests(test_dir, build_cfg, test_type, test_filter))

    return tests


def clear_test_directory(device):
    print('Clearing test directory on {}.'.format(device))
    cmd = ['rm', '-r', DEVICE_TEST_BASE_DIR]
    logger().info('%s: shell_nocheck "%s"', device.name, cmd)
    device.shell_nocheck(cmd)


def clear_test_directories(workqueue, fleet):
    for device in fleet.get_unique_devices():
        workqueue.add_task(clear_test_directory, device)

    while not workqueue.finished():
        workqueue.get_result()


def adb_has_feature(feature):
    cmd = ['adb', 'host-features']
    logger().info('check_output "%s"', ' '.join(cmd))
    output = subprocess.check_output(cmd)
    features_line = output.splitlines()[-1]
    features = features_line.split(',')
    return feature in features


def push_tests_to_device(src_dir, dest_dir, config, device, use_sync):
    print('Pushing {} tests to {}.'.format(config, device))
    logger().info('%s: mkdir %s', device.name, dest_dir)
    device.shell_nocheck(['mkdir', dest_dir])
    logger().info(
        '%s: push%s %s %s', device.name, ' --sync' if use_sync else '',
        src_dir, dest_dir)
    device.push(src_dir, dest_dir, sync=use_sync)


def push_tests_to_devices(workqueue, test_dir, devices_for_config, use_sync):
    for config, devices in devices_for_config.items():
        src_dir = os.path.join(test_dir, str(config))
        dest_dir = DEVICE_TEST_BASE_DIR
        for device in devices:
            workqueue.add_task(
                push_tests_to_device, src_dir, dest_dir, config, device,
                use_sync)

    while not workqueue.finished():
        workqueue.get_result()


def disable_verity_and_wait_for_reboot(device):
    if device.get_prop('ro.boot.veritymode') != 'enforcing':
        return

    logger().info('%s: root', device.name)
    device.root()

    logger().info('%s: disable-verity', device.name)
    cmd = ['adb', '-s', device.serial, 'disable-verity']
    # disable-verity doesn't set exit status
    _, out = ndk.subprocess.call_output(cmd)
    logger().info('%s: disable-verity:\n%s', device, out)
    if 'disabled on /' not in out:
        raise RuntimeError('{}: adb disable-verity failed:\n{}'.format(
            device, out))

    if 'reboot your device' in out:
        logger().info('%s: reboot', device.name)
        device.reboot()
        logger().info('%s: wait-for-device', device.name)
        device.wait()


def asan_device_setup(ndk_path, device):
    path = os.path.join(
        ndk_path, 'toolchains/llvm/prebuilt', ndk.hosts.get_host_tag(ndk_path),
        'bin/asan_device_setup')
    cmd = [path, '--device', device.serial]
    logger().info('%s: asan_device_setup', device.name)
    # Use call_output to keep the call quiet unless something goes wrong.
    result, out = ndk.subprocess.call_output(cmd)
    if result != 0:
        # The script sometimes fails on the first try >:(
        logger().info(
            '%s: asan_device_setup failed once, retrying', device.name)
        result, out = ndk.subprocess.call_output(cmd)
    if result != 0:
        # The script sometimes fails on the first try >:(
        result, out = ndk.subprocess.call_output(cmd)
        raise RuntimeError('{}: asan_device_setup failed:\n{}'.format(
            device, out))


def setup_asan_for_device(ndk_path, device):
    print('Performing ASAN setup for {}'.format(device))
    disable_verity_and_wait_for_reboot(device)
    asan_device_setup(ndk_path, device)


def perform_asan_setup(workqueue, ndk_path, devices):
    # asan_device_setup is a shell script, so no asan there.
    if os.name == 'nt':
        return

    for device in devices:
        if device.can_use_asan():
            workqueue.add_task(setup_asan_for_device, ndk_path, device)

    while not workqueue.finished():
        workqueue.get_result()


def run_test(test):
    return test.run()


def print_test_stats(test_groups):
    test_stats = {}
    for config, tests in test_groups.items():
        test_stats[config] = {}
        for test in tests:
            if test.build_system not in test_stats[config]:
                test_stats[config][test.build_system] = []
            test_stats[config][test.build_system].append(test)

    for config, build_system_groups in test_stats.items():
        print('Config {}:'.format(config))
        for build_system, tests in build_system_groups.items():
            print('\t{}: {} tests'.format(build_system, len(tests)))


def verify_have_all_requested_devices(fleet):
    missing_configs = fleet.get_missing()
    if len(missing_configs):
        logger().warning(
            'Missing device configurations: %s', ', '.join(missing_configs))
        return False
    return True


def find_configs_with_no_device(devices_for_config):
    return [c for c, ds in devices_for_config.items() if not ds]


def match_configs_to_devices(fleet, configs):
    devices_for_config = {config: [] for config in configs}
    for config in configs:
        for device in fleet.get_unique_devices():
            if not device.can_run_build_config(config):
                continue
            devices_for_config[config].append(device)

    return devices_for_config


def create_test_runs(test_groups, devices_for_config):
    """Creates a TestRun object for each device/test case pairing."""
    test_runs = []
    for config, test_cases in test_groups.items():
        for device in devices_for_config[config]:
            test_runs.extend([TestRun(tc, device) for tc in test_cases])
    return test_runs


def wait_for_results(report, workqueue, printer):
    while not workqueue.finished():
        result = workqueue.get_result()
        suite = result.test.build_system
        report.add_result(suite, result)
        if logger().isEnabledFor(logging.INFO):
            printer.print_result(result)
        elif result.failed():
            printer.print_result(result)


def flake_filter(result):
    if isinstance(result, testlib.UnexpectedSuccess):
        # There are no flaky successes.
        return False

    # adb might return no text at all under high load.
    if 'Did not receive exit status from test.' in result.message:
        return True

    return False


def restart_flaky_tests(report, workqueue):
    """Finds and restarts any failing flaky tests."""
    rerun_tests = report.remove_all_failing_flaky(flake_filter)
    if len(rerun_tests) > 0:
        cooldown = 10
        logger().warning(
            'Found %d flaky failures. Sleeping for %d seconds to let '
            'devices recover.', len(rerun_tests), cooldown)
        time.sleep(cooldown)

    for flaky_report in rerun_tests:
        logger().warning('Flaky test failure: %s', flaky_report.result)
        workqueue.add_task(run_test, flaky_report.result.test)


def get_config_dict(config, abis, toolchains, headers, pie):
    with open(config) as test_config_file:
        test_config = json.load(test_config_file)
    if abis is not None:
        test_config['abis'] = abis
    if toolchains is not None:
        test_config['toolchains'] = toolchains
    if headers is not None:
        test_config['headers'] = headers
    if pie is not None:
        test_config['pie'] = pie
    return test_config


def str_to_bool(s):
    if s == 'true':
        return True
    elif s == 'false':
        return False
    raise ValueError(s)


def parse_args():
    doc = ('https://android.googlesource.com/platform/ndk/+/master/'
           'docs/Testing.md')
    parser = argparse.ArgumentParser(
        epilog='See {} for more information.'.format(doc))

    config_options = parser.add_argument_group('Test Configuration Options')
    config_options.add_argument(
        '--filter', help='Only run tests that match the given pattern.')
    config_options.add_argument(
        '--abi', action='append', choices=build.lib.build_support.ALL_ABIS,
        help='Test only the given APIs.')
    config_options.add_argument(
        '--toolchain', action='append', choices=('clang', 'gcc'),
        help='Test only the given toolchains.')
    config_options.add_argument(
        '--headers', action='append', choices=('unified', 'deprecated'),
        help='Test only the given header configurations.')
    config_options.add_argument(
        '--pie', action='append', choices=(True, False), type=str_to_bool,
        help='Test only the given PIE configurations.')
    config_options.add_argument(
        '--config', type=os.path.realpath, default='qa_config.json',
        help='Path to the config file describing the test run.')

    build_options = parser.add_argument_group('Build Options')
    build_options.add_argument(
        '--rebuild', action='store_true',
        help='Build the tests before running.')
    build_options.add_argument(
        '--clean', action='store_true',
        help='Remove the out directory before building.')

    run_options = parser.add_argument_group('Test Run Options')
    run_options.add_argument(
        '--clean-device', action='store_true',
        help='Clear the device directories before syncing.')
    run_options.add_argument(
        '--require-all-devices', action='store_true',
        help='Abort if any devices specified by the config are not available.')

    display_options = parser.add_argument_group('Display Options')
    display_options.add_argument(
        '--show-all', action='store_true',
        help='Show all test results, not just failures.')
    display_options.add_argument(
        '--show-test-stats', action='store_true',
        help='Print number of tests found for each configuration.')
    display_options.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Increase log level. Defaults to logging.WARNING.')

    parser.add_argument(
        '--ndk', type=os.path.realpath, default=ndk.paths.get_install_path(),
        help='NDK to validate. Defaults to ../out/android-ndk-$RELEASE.')

    parser.add_argument(
        'test_dir', metavar='TEST_DIR', type=os.path.realpath, nargs='?',
        default=ndk.paths.path_in_out('tests'),
        help='Directory containing built tests.')

    return parser.parse_args()


class ConfigFilter(object):
    def __init__(self, test_config):
        import itertools
        test_spec = ndk.test.builder.test_spec_from_config(test_config)

        self.config_tuples = list(itertools.product(
            test_spec.abis,
            test_spec.toolchains,
            test_spec.headers_config,
            test_spec.pie_config))

    def filter(self, build_config):
        config_tuple = (
            build_config.abi,
            build_config.toolchain,
            build_config.force_deprecated_headers,
            build_config.force_pie
        )

        return config_tuple in self.config_tuples


def main():
    args = parse_args()

    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    verbosity = min(args.verbose, len(log_levels) - 1)
    log_level = log_levels[verbosity]
    logging.basicConfig(level=log_level)

    python_packages = os.path.join(args.ndk, 'python-packages')
    site.addsitedir(python_packages)

    if not os.path.exists(args.test_dir):
        sys.exit('Test directory does not exist: {}'.format(args.test_dir))

    test_config = get_config_dict(
        args.config, args.abi, args.toolchain, args.headers, args.pie)

    printer = printers.StdoutPrinter(show_all=args.show_all)
    if args.rebuild:
        report = build_tests(
            args.ndk, args.test_dir, args.clean, printer, test_config,
            args.filter)
        if report.num_tests == 0:
            sys.exit('Found no tests for filter {}.'.format(args.filter))
        printer.print_summary(report)
        if not report.successful:
            sys.exit(report.num_failed)

    test_dist_dir = os.path.join(args.test_dir, 'dist')
    test_filter = filters.TestFilter.from_string(args.filter)
    # dict of {BuildConfiguration: [Test]}
    config_filter = ConfigFilter(test_config)
    test_groups = enumerate_tests(test_dist_dir, test_filter, config_filter)
    if sum([len(tests) for tests in test_groups.values()]) == 0:
        print('Found no tests in {} for filter {}.'.format(
            test_dist_dir, args.filter))
        # As long as we *built* some tests, not having anything to run isn't a
        # failure.
        sys.exit(not args.rebuild)

    if args.show_test_stats:
        print_test_stats(test_groups)

    # For finding devices, we have a list of devices we want to run on in our
    # config file. If we did away with this list, we could instead run every
    # test on every compatible device, but in the event of multiple similar
    # devices, that's a lot of duplication. The list keeps us from running
    # tests on android-24 and android-25, which don't have meaningful
    # differences.
    #
    # The list also makes sure we don't miss any devices that we expect to run
    # on.
    #
    # The other thing we need to verify is that each test we find is run at
    # least once.
    #
    # Get the list of all devices. Prune this by the requested device
    # configuration. For each requested configuration that was not found, print
    # a warning. Then compare that list of devices against all our tests and
    # make sure each test is claimed by at least one device. For each
    # configuration that is unclaimed, print a warning.
    fleet = ndk.test.devices.find_devices(test_config['devices'])
    have_all_devices = verify_have_all_requested_devices(fleet)
    if args.require_all_devices and not have_all_devices:
        sys.exit('Some requested devices were not available. Quitting.')

    devices_for_config = match_configs_to_devices(fleet, test_groups.keys())
    for config in find_configs_with_no_device(devices_for_config):
        logger().warning('No device found for %s.', config)
    test_runs = create_test_runs(test_groups, devices_for_config)

    all_used_devices = []
    for devices in devices_for_config.values():
        all_used_devices.extend(devices)
    all_used_devices = sorted(list(set(all_used_devices)))

    report = ndk.test.report.Report()
    workqueue = ndk.workqueue.WorkQueue()
    try:
        if args.clean_device:
            clear_test_directories(workqueue, fleet)
        can_use_sync = adb_has_feature('push_sync')
        push_tests_to_devices(
            workqueue, test_dist_dir, devices_for_config, can_use_sync)

        perform_asan_setup(workqueue, args.ndk, all_used_devices)

        # Shuffle the test runs to distribute the load more evenly. These are
        # ordered by (build config, device, test), so most of the tests running
        # at any given point in time are all running on the same device.
        random.shuffle(test_runs)
        for test in test_runs:
            workqueue.add_task(run_test, test)

        wait_for_results(report, workqueue, printer)
        restart_flaky_tests(report, workqueue)
        wait_for_results(report, workqueue, printer)

        printer.print_summary(report)
    finally:
        workqueue.terminate()
        workqueue.join()

    sys.exit(not report.successful)


if __name__ == '__main__':
    main()
