#!/usr/bin/env python
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
"""Runs the test suite over a set of devices."""
from __future__ import print_function

import argparse
import distutils.spawn
import logging
import os
import re
import shutil
import signal
import site
import subprocess
import sys
import yaml

import ndk.debug
import ndk.notify
import ndk.paths


THIS_DIR = os.path.realpath(os.path.dirname(__file__))


class Device(object):
    def __init__(self, serial, name, version, build_id, abis, is_emulator):
        self.serial = serial
        self.name = name
        self.version = version
        self.build_id = build_id
        self.abis = abis
        self.is_emulator = is_emulator

    def __str__(self):
        return 'android-{} {} {} {}'.format(
            self.version, self.name, self.serial, self.build_id)


class DeviceFleet(object):
    def __init__(self, test_configurations):
        """Initializes a device fleet.

        Args:
            test_configurations: Dict mapping API levels to a list of ABIs to
                test for that API level. Example:

                    {
                        15: ['armeabi', 'armeabi-v7a'],
                        16: ['armeabi', 'armeabi-v7a', 'x86'],
                    }
        """
        self.devices = {}
        for api, abis in test_configurations.items():
            self.devices[api] = {abi: None for abi in abis}

    def add_device(self, device):
        if device.version not in self.devices:
            print('Ignoring device for unwanted API level: {}'.format(device))
            return

        same_version = self.devices[device.version]
        for abi, current_device in same_version.iteritems():
            # This device can't fulfill this ABI.
            if abi not in device.abis:
                continue

            # Never houdini.
            if abi.startswith('armeabi') and 'x86' in device.abis:
                continue

            # Anything is better than nothing.
            if current_device is None:
                self.devices[device.version][abi] = device
                continue

            # The emulator images have actually been changed over time, so the
            # devices are more trustworthy.
            if current_device.is_emulator and not device.is_emulator:
                self.devices[device.version][abi] = device

    def get_device(self, version, abi):
        return self.devices[version][abi]

    def get_missing(self):
        missing = []
        for version, abis in self.devices.iteritems():
            for abi, device in abis.iteritems():
                if device is None:
                    missing.append('android-{} {}'.format(version, abi))
        return missing

    def get_versions(self):
        return self.devices.keys()

    def get_abis(self, version):
        return self.devices[version].keys()


def get_device_abis(properties):
    # 64-bit devices list their ABIs differently than 32-bit devices. Check all
    # the possible places for stashing ABI info and merge them.
    abi_properties = [
        'ro.product.cpu.abi',
        'ro.product.cpu.abi2',
        'ro.product.cpu.abilist',
    ]
    abis = set()
    for abi_prop in abi_properties:
        if abi_prop in properties:
            abis.update(properties[abi_prop].split(','))

    return sorted(list(abis))


def get_device_details(serial):
    import adb  # pylint: disable=import-error
    props = adb.get_device(serial).get_props()
    name = props['ro.product.name']
    version = int(props['ro.build.version.sdk'])
    supported_abis = get_device_abis(props)
    build_id = props['ro.build.id']
    is_emulator = props.get('ro.build.characteristics') == 'emulator'
    return Device(serial, name, version, build_id, supported_abis, is_emulator)


def find_devices(sought_devices):
    """Detects connected devices and returns a set for testing.

    We get a list of devices by scanning the output of `adb devices`. We want
    to run the tests for the cross product of the following configurations:

    ABIs: {armeabi, armeabi-v7a, arm64-v8a, mips, mips64, x86, x86_64}
    Platform versions: {android-10, android-16, android-21}
    Toolchains: {clang, gcc}

    Note that not all ABIs are available for every platform version. There are
    no 64-bit ABIs before android-21, and there were no MIPS ABIs for
    android-10.
    """
    if distutils.spawn.find_executable('adb') is None:
        raise RuntimeError('Could not find adb.')

    # We could get the device name from `adb devices -l`, but we need to
    # getprop to find other details anyway, and older devices don't report
    # their names properly (nakasi on android-16, for example).
    p = subprocess.Popen(['adb', 'devices'], stdout=subprocess.PIPE)
    out, _ = p.communicate()
    if p.returncode != 0:
        raise RuntimeError('Failed to get list of devices from adb.')

    # The first line of `adb devices` just says "List of attached devices", so
    # skip that.
    fleet = DeviceFleet(sought_devices)
    for line in out.split('\n')[1:]:
        if not line.strip():
            continue

        serial, _ = re.split(r'\s+', line, maxsplit=1)

        if 'offline' in line:
            print('Ignoring offline device: ' + serial)
            continue
        if 'unauthorized' in line:
            print('Ignoring unauthorized device: ' + serial)
            continue

        device = get_device_details(serial)
        print('Found device {}'.format(device))
        fleet.add_device(device)

    return fleet


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'ndk', metavar='NDK', type=os.path.realpath, nargs='?',
        help='NDK to validate. Defaults to ../out/android-ndk-$RELEASE.')

    parser.add_argument(
        '--abi', dest='abis', action='append',
        help=('ABIs to test. Defaults to all available for the connected '
              'devices.'))
    parser.add_argument(
        '--platform', dest='platforms', action='append', type=int,
        help=('Device API levels to test. Must be a subset of '
              'DeviceFleet.devices.'))
    parser.add_argument(
        '--toolchain', dest='toolchains', action='append',
        choices=('clang', '4.9'), help='Toolchains to test.')
    parser.add_argument(
        '--headers-config', dest='headers_configs', action='append',
        choices=('unified', 'deprecated'), help='Headers configs to test.')

    import tests.testlib
    parser.add_argument(
        '--suite', dest='suites', action='append',
        choices=tests.testlib.ALL_SUITES, help='Test suites to run.')

    parser.add_argument(
        '--filter', help='Only run tests that match the given pattern.')
    parser.add_argument(
        '--log-dir', type=os.path.realpath, default='test-logs',
        help='Directory to store test logs.')
    parser.add_argument(
        '--config', type=os.path.realpath, default='qa_config.yaml',
        help='Path to the config file describing the test run.')
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Increase log level. Defaults to logging.WARNING.')

    return parser.parse_args()


def get_aggregate_results(details):
    tests = {}
    for config, report in details.iteritems():
        for suite, suite_report in report.by_suite().items():
            for test_report in suite_report.all_failed:
                name = '.'.join([suite, test_report.result.test.name])
                if name not in tests:
                    tests[name] = []
                tests[name].append((config, test_report.result))
    return tests


def print_aggregate_details(details, use_color):
    tests = get_aggregate_results(details)
    for test_name, configs in tests.iteritems():
        # We might be printing a lot of crap here, so let's be obvious about
        # where each test starts.
        print('BEGIN TEST RESULT: ' + test_name)
        print('=' * 80)

        for config, result in configs:
            print('FAILED {}:'.format(config))
            print(result.to_string(colored=use_color))


def main():
    if sys.platform != 'win32':
        ndk.debug.register_debug_handler(signal.SIGUSR1)
        ndk.debug.register_trace_handler(signal.SIGUSR2)

    args = parse_args()

    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    verbosity = min(args.verbose, len(log_levels) - 1)
    log_level = log_levels[verbosity]
    logging.basicConfig(level=log_level)

    os.chdir(THIS_DIR)

    if args.ndk is None:
        args.ndk = ndk.paths.get_install_path()

    # We need to do this here rather than at the top because we load the module
    # from a path that is given on the command line. We load it from the NDK
    # given on the command line so this script can be run even without a full
    # platform checkout.
    site.addsitedir(os.path.join(args.ndk, 'python-packages'))

    ndk_build_path = os.path.join(args.ndk, 'ndk-build')
    if os.name == 'nt':
        ndk_build_path += '.cmd'
    if not os.path.exists(ndk_build_path):
        sys.exit(ndk_build_path + ' does not exist.')

    with open(args.config) as test_config_file:
        test_config = yaml.load(test_config_file)

    fleet = find_devices(test_config['devices'])
    print('Test configuration:')
    for version in sorted(fleet.get_versions()):
        print('\tandroid-{}:'.format(version))
        for abi in sorted(fleet.get_abis(version)):
            print('\t\t{}: {}'.format(abi, fleet.get_device(version, abi)))
    missing_configs = fleet.get_missing()
    if len(missing_configs):
        print('Missing configurations: {}'.format(', '.join(missing_configs)))

    if os.path.exists(args.log_dir):
        shutil.rmtree(args.log_dir)
    os.makedirs(args.log_dir)

    if args.headers_configs is None:
        headers_configs = args.headers_configs
    else:
        headers_configs = [c == 'deprecated' for c in args.headers_configs]

    use_color = sys.stdin.isatty() and os.name != 'nt'
    with ndk.paths.temp_dir_in_out('validate-out') as out_dir:
        import tests.runners
        good, details = tests.runners.run_for_fleet(
            args.ndk, fleet, out_dir, args.log_dir, args.filter,
            args.platforms, args.abis, args.toolchains, headers_configs,
            args.suites, use_color)

    print_aggregate_details(details, use_color)

    subject = 'NDK Testing {}!'.format('Passed' if good else 'Failed')
    ndk.notify.toast(subject)

    sys.exit(not good)


if __name__ == '__main__':
    main()
