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
import logging
import os
import shutil
import signal
import site
import sys
import yaml

import ndk.debug
import ndk.notify
import ndk.paths
import ndk.test.devices


THIS_DIR = os.path.realpath(os.path.dirname(__file__))


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

    fleet = ndk.test.devices.find_devices(test_config['devices'])
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
            args.ndk, fleet, out_dir, args.filter, args.platforms, args.abis,
            args.toolchains, headers_configs, args.suites, use_color)

    print_aggregate_details(details, use_color)

    subject = 'NDK Testing {}!'.format('Passed' if good else 'Failed')
    ndk.notify.toast(subject)

    sys.exit(not good)


if __name__ == '__main__':
    main()
