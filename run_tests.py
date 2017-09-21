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
import contextlib
import json
import logging
import multiprocessing
import os
import posixpath
import random
import site
import subprocess
import sys
import termios
import time
import traceback

import build.lib.build_support
import ndk.ansi
import ndk.notify
import ndk.paths
import ndk.subprocess
import ndk.test.builder
import ndk.test.devices
import ndk.test.report
import ndk.test.result
import ndk.test.spec
import ndk.test.ui
import ndk.ui
import ndk.timer
import ndk.workqueue

import tests.filters as filters
import tests.printers as printers
import tests.testlib as testlib


DEVICE_TEST_BASE_DIR = '/data/local/tmp/tests'


def logger():
    """Returns the module logger."""
    return logging.getLogger(__name__)


def shell_nocheck_wrap_errors(device, cmd):
    """Invokes device.shell_nocheck and wraps exceptions as failed commands."""
    try:
        return device.shell_nocheck(cmd)
    except RuntimeError as ex:
        return 1, traceback.format_exc(ex), ''


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
        config = self.check_unsupported(device)
        if config is not None:
            message = 'test unsupported for {}'.format(config)
            return ndk.test.result.Skipped(self, message)

        cmd = 'cd {} && LD_LIBRARY_PATH={} ./{} 2>&1'.format(
            self.device_dir, self.device_dir, self.executable)
        logger().info('%s: shell_nocheck "%s"', device.name, cmd)
        return shell_nocheck_wrap_errors(device, [cmd])


class LibcxxTestCase(TestCase):
    """A libc++ test case built by LIT.

    LIT's test structure doesn't map cleanly to ours; they have a hierarchical
    test structure. The top level contains a single "libc++" directory. In that
    directory is where shared libraries common to all tests are placed. That
    directory and any under it may contain test executables (always suffixed
    with ".exe") or test data (always suffixed with ".dat").
    """
    def __init__(self, suite, executable, config, device_dir):
        # Tests in the top level don't need any mangling to match the filters.
        if suite == 'libc++':
            filter_name = executable
        else:
            filter_name = suite[len('libc++/'):] + executable

        # The executable name ends with .exe. Remove that so it matches the
        # filter that would be used to build the test.
        name = '.'.join(['libc++', filter_name[:-4]])
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
        libcxx_so_dir = posixpath.join(
            DEVICE_TEST_BASE_DIR, str(self.config), 'libcxx/libc++')
        cmd = 'cd {} && LD_LIBRARY_PATH={} ./{} 2>&1'.format(
            self.device_dir, libcxx_so_dir, self.executable)
        logger().info('%s: shell_nocheck "%s"', device.name, cmd)
        return shell_nocheck_wrap_errors(device, [cmd])


class TestRun(object):
    """A test case mapped to the device group it will run on."""
    def __init__(self, test_case, device_group):
        self.test_case = test_case
        self.device_group = device_group

    @property
    def name(self):
        return self.test_case.name

    @property
    def build_system(self):
        return self.test_case.build_system

    @property
    def config(self):
        return self.test_case.config

    def make_result(self, adb_result_tuple, device):
        status, out, _ = adb_result_tuple
        if status == 0:
            result = ndk.test.result.Success(self)
        else:
            out = '\n'.join([str(device), out])
            result = ndk.test.result.Failure(self, out)
        return self.fixup_xfail(result, device)

    def fixup_xfail(self, result, device):
        config, bug = self.test_case.check_broken(device)
        if config is not None:
            if result.failed():
                return ndk.test.result.ExpectedFailure(self, config, bug)
            elif result.passed():
                return ndk.test.result.UnexpectedSuccess(self, config, bug)
            raise ValueError('Test result must have either failed or passed.')
        return result

    def run(self, device):
        config = self.test_case.check_unsupported(device)
        if config is not None:
            message = 'test unsupported for {}'.format(config)
            return ndk.test.result.Skipped(self, message)
        return self.make_result(self.test_case.run(device), device)


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
        device_relpath = test_relpath
        if sys.platform == 'win32':
            device_relpath = device_relpath.replace('\\', '/')
        device_dir = posixpath.join(DEVICE_TEST_BASE_DIR, device_relpath)
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

            # Our file has a .exe extension, but the name should match the
            # source file for the filters to work.
            test_name = test_file[:-4]

            # Tests in the top level don't need any mangling to match the
            # filters.
            if not suite_name == 'libc++':
                if not suite_name.startswith('libc++/'):
                    raise ValueError(suite_name)
                assert suite_name.startswith('libc++/')
                # According to the test runner, these are all part of the
                # "libc++" test, and the rest of the data is the subtest name.
                # i.e.  libc++/foo/bar/baz.cpp.exe is actually
                # libc++.foo/bar/baz.cpp.  Matching this expectation here
                # allows us to use the same filter string for running the tests
                # as for building the tests.
                test_path = suite_name[len('libc++/'):]
                test_name = '/'.join([test_path, test_name])

            filter_name = '.'.join(['libc++', test_name])
            if not test_filter.filter(filter_name):
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


def clear_test_directory(_worker, device):
    print('Clearing test directory on {}.'.format(device))
    cmd = ['rm', '-r', DEVICE_TEST_BASE_DIR]
    logger().info('%s: shell_nocheck "%s"', device.name, cmd)
    device.shell_nocheck(cmd)


def clear_test_directories(workqueue, fleet):
    for group in fleet.get_unique_device_groups():
        for device in group.devices:
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


def push_tests_to_device(worker, src_dir, dest_dir, config, device,
                         use_sync):
    worker.status = 'Pushing {} tests to {}.'.format(config, device)
    logger().info('%s: mkdir %s', device.name, dest_dir)
    device.shell_nocheck(['mkdir', dest_dir])
    logger().info(
        '%s: push%s %s %s', device.name, ' --sync' if use_sync else '',
        src_dir, dest_dir)
    device.push(src_dir, dest_dir, sync=use_sync)
    if sys.platform == 'win32':
        device.shell(['chmod', '-R', '777', dest_dir])


def finish_workqueue_with_ui(workqueue):
    console = ndk.ansi.get_console()
    ui = ndk.ui.get_work_queue_ui(console, workqueue)
    with ndk.ansi.disable_terminal_echo(sys.stdin):
        with console.cursor_hide_context():
            ui.draw()
            while not workqueue.finished():
                workqueue.get_result()
                ui.draw()
            ui.clear()


def push_tests_to_devices(workqueue, test_dir, groups_for_config, use_sync):
    dest_dir = DEVICE_TEST_BASE_DIR
    for config, groups in groups_for_config.items():
        src_dir = os.path.join(test_dir, str(config))
        for group in groups:
            for device in group.devices:
                workqueue.add_task(
                    push_tests_to_device, src_dir, dest_dir, config, device,
                    use_sync)

    finish_workqueue_with_ui(workqueue)
    print('Finished pushing tests')


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


def setup_asan_for_device(worker, ndk_path, device):
    worker.status = 'Performing ASAN setup for {}'.format(device)
    disable_verity_and_wait_for_reboot(device)
    asan_device_setup(ndk_path, device)


def perform_asan_setup(workqueue, ndk_path, groups_for_config):
    # asan_device_setup is a shell script, so no asan there.
    if os.name == 'nt':
        return

    devices = []
    for groups in groups_for_config.values():
        for group in groups:
            devices.extend(group.devices)
    devices = sorted(list(set(devices)))

    for device in devices:
        if device.can_use_asan():
            workqueue.add_task(setup_asan_for_device, ndk_path, device)

    finish_workqueue_with_ui(workqueue)
    print('Finished ASAN setup')


def run_test(worker, test):
    device = worker.data[0]
    worker.status = 'Running {}'.format(test.name)
    return test.run(device)


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


def find_configs_with_no_device(groups_for_config):
    return [c for c, gs in groups_for_config.items() if not gs]


def match_configs_to_device_groups(fleet, configs):
    groups_for_config = {config: [] for config in configs}
    for config in configs:
        for group in fleet.get_unique_device_groups():
            # All devices in the group are identical.
            device = group.devices[0]
            if not device.can_run_build_config(config):
                continue
            groups_for_config[config].append(group)

    return groups_for_config


def pair_test_runs(test_groups, groups_for_config):
    """Creates a TestRun object for each device/test case pairing."""
    test_runs = []
    for config, test_cases in test_groups.items():
        if not test_cases:
            continue

        for group in groups_for_config[config]:
            test_runs.extend([TestRun(tc, group) for tc in test_cases])
    return test_runs


def wait_for_results(report, workqueue, printer):
    console = ndk.ansi.get_console()
    ui = ndk.test.ui.get_test_progress_ui(console, workqueue)
    with ndk.ansi.disable_terminal_echo(sys.stdin):
        with console.cursor_hide_context():
            while not workqueue.finished():
                result = workqueue.get_result()
                suite = result.test.build_system
                report.add_result(suite, result)
                if logger().isEnabledFor(logging.INFO):
                    ui.clear()
                    printer.print_result(result)
                elif result.failed():
                    ui.clear()
                    printer.print_result(result)
                ui.draw()
            ui.clear()


def flake_filter(result):
    if isinstance(result, testlib.UnexpectedSuccess):
        # There are no flaky successes.
        return False

    # adb might return no text at all under high load.
    if 'Could not find exit status in shell output.' in result.message:
        return True

    # These libc++ tests expect to complete in a specific amount of time,
    # and commonly fail under high load.
    name = result.test.name
    if 'libc++.libcxx/thread' in name or 'libc++.std/thread' in name:
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
        group = flaky_report.result.test.device_group
        workqueue.add_task(group, run_test, flaky_report.result.test)


def get_config_dict(config, abis, toolchains, pie):
    with open(config) as test_config_file:
        test_config = json.load(test_config_file)
    if abis is not None:
        test_config['abis'] = abis
    if toolchains is not None:
        test_config['toolchains'] = toolchains
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
            test_spec.pie_config))

    def filter(self, build_config):
        config_tuple = (
            build_config.abi,
            build_config.toolchain,
            build_config.force_pie
        )

        return config_tuple in self.config_tuples


class ShardingWorkQueue(object):
    def __init__(self, device_groups, procs_per_device):
        self.manager = multiprocessing.Manager()
        self.result_queue = self.manager.Queue()
        self.task_queues = {}
        self.work_queues = []
        self.num_tasks = 0
        for group in device_groups:
            self.task_queues[group] = self.manager.Queue()
            for device in group.devices:
                self.work_queues.append(
                    ndk.workqueue.WorkQueue(
                        procs_per_device, task_queue=self.task_queues[group],
                        result_queue=self.result_queue, worker_data=[device]))

    def add_task(self, group, func, *args, **kwargs):
        self.task_queues[group].put(
            ndk.workqueue.Task(func, args, kwargs))
        self.num_tasks += 1

    def get_result(self):
        """Gets a result from the queue, blocking until one is available."""
        result = self.result_queue.get()
        if type(result) == ndk.workqueue.TaskError:
            raise result
        self.num_tasks -= 1
        return result

    def terminate(self):
        for work_queue in self.work_queues:
            work_queue.terminate()

    def join(self):
        for work_queue in self.work_queues:
            work_queue.join()

    def finished(self):
        """Returns True if all tasks have completed execution."""
        return self.num_tasks == 0


def main():
    total_timer = ndk.timer.Timer()
    total_timer.start()

    args = parse_args()

    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    verbosity = min(args.verbose, len(log_levels) - 1)
    log_level = log_levels[verbosity]
    logging.basicConfig(level=log_level)

    python_packages = os.path.join(args.ndk, 'python-packages')
    site.addsitedir(python_packages)

    if not os.path.exists(args.test_dir):
        if args.rebuild:
            os.makedirs(args.test_dir)
        else:
            sys.exit('Test directory does not exist: {}'.format(args.test_dir))

    test_config = get_config_dict(
        args.config, args.abi, args.toolchain, args.pie)

    printer = printers.StdoutPrinter(show_all=args.show_all)
    build_timer = ndk.timer.Timer()
    with build_timer:
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
    test_discovery_timer = ndk.timer.Timer()
    with test_discovery_timer:
        test_groups = enumerate_tests(
            test_dist_dir, test_filter, config_filter)

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
    workqueue = ndk.workqueue.WorkQueue()
    try:
        device_discovery_timer = ndk.timer.Timer()
        with device_discovery_timer:
            fleet = ndk.test.devices.find_devices(
                test_config['devices'], workqueue)
        have_all_devices = verify_have_all_requested_devices(fleet)
        if args.require_all_devices and not have_all_devices:
            sys.exit('Some requested devices were not available. Quitting.')

        groups_for_config = match_configs_to_device_groups(
            fleet, test_groups.keys())
        for config in find_configs_with_no_device(groups_for_config):
            logger().warning('No device found for %s.', config)

        report = ndk.test.report.Report()
        clean_device_timer = ndk.timer.Timer()
        with clean_device_timer:
            if args.clean_device:
                clear_test_directories(workqueue, fleet)
        can_use_sync = adb_has_feature('push_sync')
        push_timer = ndk.timer.Timer()
        with push_timer:
            push_tests_to_devices(
                workqueue, test_dist_dir, groups_for_config, can_use_sync)

        asan_setup_timer = ndk.timer.Timer()
        with asan_setup_timer:
            perform_asan_setup(workqueue, args.ndk, groups_for_config)
    finally:
        workqueue.terminate()
        workqueue.join()

    shard_queue = ShardingWorkQueue(fleet.get_unique_device_groups(), 4)
    try:
        # Need an input queue per device group, a single result queue, and a
        # pool of threads per device.

        # Shuffle the test runs to distribute the load more evenly. These are
        # ordered by (build config, device, test), so most of the tests running
        # at any given point in time are all running on the same device.
        test_runs = pair_test_runs(test_groups, groups_for_config)
        random.shuffle(test_runs)
        test_run_timer = ndk.timer.Timer()
        with test_run_timer:
            for test_run in test_runs:
                shard_queue.add_task(test_run.device_group, run_test, test_run)

            wait_for_results(report, shard_queue, printer)
            restart_flaky_tests(report, shard_queue)
            wait_for_results(report, shard_queue, printer)

        printer.print_summary(report)
    finally:
        shard_queue.terminate()
        shard_queue.join()

    total_timer.finish()

    print('Finished {}'.format(
        'successfully' if report.successful else 'unsuccessfully'))
    if args.rebuild:
        print('Build: {}'.format(build_timer.duration))
    print('Test discovery: {}'.format(test_discovery_timer.duration))
    print('Device discovery: {}'.format(device_discovery_timer.duration))
    if args.clean_device:
        print('Clean device: {}'.format(clean_device_timer.duration))
    print('Push: {}'.format(push_timer.duration))
    print('ASAN setup: {}'.format(asan_setup_timer.duration))
    print('Run: {}'.format(test_run_timer.duration))
    print('Total: {}'.format(total_timer.duration))

    subject = 'NDK Testing {}!'.format(
        'Passed' if report.successful else 'Failed')
    body = 'Testing finished in {}'.format(total_timer.duration)
    ndk.notify.toast(subject, body)

    sys.exit(not report.successful)


if __name__ == '__main__':
    main()
