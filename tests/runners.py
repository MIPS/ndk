#
# Copyright (C) 2016 The Android Open Source Project
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

import logging
import os
import subprocess
import sys

import adb  # pylint: disable=import-error
import build.lib.build_support
import tests.filters
import tests.printers
import tests.ndk
import tests.testlib
import tests.util


def logger():
    return logging.getLogger(__name__)


def get_device_abis(device):
    # 64-bit devices list their ABIs differently than 32-bit devices. Check all
    # the possible places for stashing ABI info and merge them.
    abi_properties = [
        'ro.product.cpu.abi',
        'ro.product.cpu.abi2',
        'ro.product.cpu.abilist',
    ]
    abis = set()
    properties = device.get_props()
    for abi_prop in abi_properties:
        if abi_prop in properties:
            abis.update(properties[abi_prop].split(','))

    return sorted(list(abis))


def check_adb_works_or_die(device, abi):
    supported_abis = get_device_abis(device)
    if abi is not None and abi not in supported_abis:
        msg = ('The test device ({}) does not support the requested ABI '
               '({}).\nSupported ABIs: {}'.format(device.serial, abi,
                                                  ', '.join(supported_abis)))
        sys.exit(msg)


def can_use_asan(device, abi, api, toolchain):
    # ASAN is currently only supported for 32-bit ARM and x86...
    if not abi.startswith('armeabi') and not abi == 'x86':
        logger().info('Cannot use ASAN: unsupported ABI (%s)', abi)
        return False

    # From non-Windows (asan_device_setup is a shell script)...
    if os.name == 'nt':
        logger().info('Cannot use ASAN: Windows is not supported')
        return False

    # On KitKat and newer...
    if api < 19:
        logger().info('Cannot use ASAN: device is too old '
                      '(is android-%s, minimum android-19)', api)
        return False

    # When using clang...
    if toolchain != 'clang':
        logger().info('Cannot use ASAN: GCC is not supprted')
        return False

    # On rooted devices.
    if int(device.get_prop('ro.debuggable')) == 0:
        logger().info('Cannot use ASAN: device must be rooted')
        return False

    # Fugu's system image doesn't have enough space left for even the ASAN
    # library.
    if device.get_prop('ro.product.name') == 'fugu':
        logger().info('Cannot use ASAN: system partition full')
        return False

    return True


def asan_device_setup():
    path = os.path.join(
        os.environ['NDK'], 'toolchains', 'llvm', 'prebuilt',
        tests.ndk.get_host_tag(), 'bin', 'asan_device_setup')
    try:
        # Don't want to use check_call because we want to keep this quiet
        # unless there's a problem.
        subprocess.check_output([path], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        print(ex.output)
        raise ex


class ResultStats(object):
    def __init__(self, suites, results):
        self.num_tests = sum(len(s) for s in results.values())

        zero_stats = {'pass': 0, 'skip': 0, 'fail': 0}
        self.global_stats = dict(zero_stats)
        self.suite_stats = {suite: dict(zero_stats) for suite in suites}
        self._analyze_results(results)

    def _analyze_results(self, results):
        for suite, test_results in results.items():
            for result in test_results:
                if result.failed():
                    self.suite_stats[suite]['fail'] += 1
                    self.global_stats['fail'] += 1
                elif result.passed():
                    self.suite_stats[suite]['pass'] += 1
                    self.global_stats['pass'] += 1
                else:
                    self.suite_stats[suite]['skip'] += 1
                    self.global_stats['skip'] += 1


def run_single_configuration(ndk_path, out_dir, printer, abi, toolchain,
                             build_api_level=None, verbose_build=False,
                             suites=None, test_filter=None,
                             device_serial=None, skip_run=False,
                             force_deprecated_headers=False):
    """Runs all the tests for the given configuration.

    Sets up the necessary build flags and environment, checks that the device
    under test is in working order and performs device setup (if running device
    tests), and finally runs the tests for the selected suites.

    Args:
        ndk_path: Absolute path the the NDK being tested.
        out_dir: Directory to use when building tests.
        printer: Instance of printers.Printer that will be used to print test
            results.
        abi: ABI to test against.
        toolchain: Toolchain to build with.
        build_api_level: API level to build against. If None, will default to
            the value set in the test's Application.mk, or ndk-build's default.
        verbose_build: Show verbose output from ndk-build and cmake.
        suites: Set of strings denoting which test suites to run. Possible
            values are 'build' and 'device'. If None, will run all suites.
        test_filter: Filter string for selecting a subset of tests.
        device_serial: Serial number of the device to use for device tests. If
            none, will try to find a device from ANDROID_SERIAL or a unique
            attached device.
        skip_run: Skip running the tests; just build. Useful for post-build
            steps if CI doesn't have the device available.
        force_deprecated_headers: Set `APP_DEPRECATED_HEADERS=true` for every
            build.

    Returns:
        ndk.test.Report describing the test results.
    """
    if suites is None:
        suites = tests.testlib.ALL_SUITES

    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    os.environ['NDK'] = ndk_path

    if verbose_build:
        # Don't decrease our log level.
        root_logger = logging.getLogger()
        if root_logger.getEffectiveLevel() != logging.DEBUG:
            root_logger.setLevel(logging.INFO)

    force_pie = False

    # Do this early so we find any device issues now rather than after we've
    # run all the build tests.
    have_device_suites = 'device' in suites or 'libc++' in suites
    if have_device_suites and not skip_run:
        device = adb.get_device(device_serial)
        check_adb_works_or_die(device, abi)
        device_api_level = int(device.get_prop('ro.build.version.sdk'))

        # PIE is required in L. All of the device tests are written toward the
        # ndk-build defaults, so we need to inform the build that we need PIE
        # if we're running on a newer device.
        if device_api_level >= 21:
            force_pie = True

        os.environ['ANDROID_SERIAL'] = device.serial

        if can_use_asan(device, abi, device_api_level, toolchain):
            asan_device_setup()

        # Do this as part of initialization rather than with a `mkdir -p` later
        # because Gingerbread didn't actually support -p :(
        device.shell_nocheck(['rm -r /data/local/tmp/ndk-tests 2>&1'])
        device.shell(['mkdir /data/local/tmp/ndk-tests 2>&1'])
        device.shell_nocheck(['rm -r /data/local/tmp/cmake-tests 2>&1'])
        device.shell(['mkdir /data/local/tmp/cmake-tests 2>&1'])
    elif skip_run:
        # We need to fake these if we're skipping running the tests. Set device
        # to None so any attempt to interact with it will raise an error, and
        # set the API level to the minimum supported by the ABI so
        # test_config.py checks still behave as expected.
        device = None
        device_api_level = build.lib.build_support.minimum_platform_level(abi)

    runner = tests.testlib.TestRunner(printer)
    if 'build' in suites:
        build_scanner = tests.testlib.BuildTestScanner()
        build_scanner.add_build_configuration(
            abi, build_api_level, toolchain, force_pie, verbose_build,
            force_deprecated_headers)
        runner.add_suite('build', 'build', build_scanner)
    if 'device' in suites:
        device_scanner = tests.testlib.DeviceTestScanner()
        device_scanner.add_device_configuration(
            abi, build_api_level, toolchain, force_pie, verbose_build,
            force_deprecated_headers, device, device_api_level, skip_run)
        runner.add_suite('device', 'device', device_scanner)
    if 'libc++' in suites:
        libcxx_scanner = tests.testlib.LibcxxTestScanner()
        libcxx_scanner.add_device_configuration(
            abi, build_api_level, toolchain, force_pie, verbose_build,
            force_deprecated_headers, device, device_api_level, skip_run)
        runner.add_suite('libc++', 'libc++', libcxx_scanner)

    test_filters = tests.filters.TestFilter.from_string(test_filter)
    report = runner.run(out_dir, out_dir, test_filters)
    return report


def get_headers_text(deprecated_headers):
    return 'deprecated' if deprecated_headers else 'unified'


def run_tests(ndk_path, device, abi, toolchain, out_dir, test_filter,
              force_deprecated_headers, suites, use_color):
    test_desc = '{} {} tests with {} headers for {}'.format(
        toolchain, abi, get_headers_text(force_deprecated_headers), device)
    print('Running {}... '.format(test_desc))
    sys.stdout.flush()

    printer = tests.printers.StdoutPrinter(use_color=use_color, quiet=True)
    report = run_single_configuration(
        ndk_path, out_dir, printer, abi, toolchain,
        device_serial=device.serial, test_filter=test_filter,
        force_deprecated_headers=force_deprecated_headers, suites=suites)
    print('{} {}'.format(
        'PASS' if report.successful else 'FAIL', test_desc))
    return report


def run_for_fleet(ndk_path, fleet, out_dir, test_filter, versions, abis,
                  toolchains, headers_configs, suites, use_color=False):
    # Note that we are duplicating some testing here.
    #
    # * The build tests only vary per-device by the PIE configuration, so we
    #   only need to run them twice per ABI/toolchain.
    # * The build tests are already run as a part of the build process.
    results = []
    details = {}
    good = True
    configurations = []

    if versions is None:
        versions = fleet.get_versions()
    if abis is None:
        abis = build.lib.build_support.ALL_ABIS
    if toolchains is None:
        toolchains = ('clang', '4.9')
    if headers_configs is None:
        headers_configs = (False, True)
    if suites is None:
        suites = tests.testlib.ALL_SUITES

    for version in versions:
        for abi in fleet.get_abis(version):
            if abi not in abis:
                continue

            device = fleet.get_device(version, abi)
            for toolchain in toolchains:
                for deprecated_headers in headers_configs:
                    if device is None:
                        results.append('android-{} {} {}: {}'.format(
                            version, abi, toolchain, 'SKIP'))
                        continue
                    configurations.append(
                        (version, abi, toolchain, deprecated_headers, device))

    for version, abi, toolchain, deprecated_headers, device in configurations:
        config_name = 'android-{} {} {} {}-headers'.format(
            version, abi, toolchain, get_headers_text(deprecated_headers))
        details[config_name] = None

        report = run_tests(
            ndk_path, device, abi, toolchain, out_dir, test_filter,
            deprecated_headers, suites, use_color)
        pass_label = tests.util.maybe_color('PASS', 'green', use_color)
        fail_label = tests.util.maybe_color('FAIL', 'red', use_color)
        results.append('{}: {}'.format(
            config_name, pass_label if report.successful else fail_label))
        details[config_name] = report
        if not report.successful:
            good = False

    print('\n'.join(results))
    return good, details
