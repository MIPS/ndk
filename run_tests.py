#!/usr/bin/env python
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
"""Runs all NDK tests.

TODO: Handle default ABI case.
The old test script would build and test all ABIs listed in APP_ABI in a single
invocation if an explicit ABI was not given. Currently this will fall down over
that case. I've written most of the code to handle this, but I decided to
factor that for-each up several levels because it was going to make the device
tests rather messy and I haven't finished doing that yet.
"""
from __future__ import print_function

import argparse
import atexit
import inspect
import logging
import os
import re
import shutil
import signal
import site
import sys
import tempfile

import build.lib.build_support
import ndk.debug
import ndk.notify
import ndk.paths

THIS_DIR = os.path.realpath(os.path.dirname(__file__))


SUPPORTED_ABIS = (
    'armeabi',
    'armeabi-v7a',
    'arm64-v8a',
    'mips',
    'mips64',
    'x86',
    'x86_64',
)


# TODO(danalbert): How much time do we actually save by not running these?
LONG_TESTS = (
    'prebuild-stlport',
    'test-stlport',
    'test-gnustl-full',
    'test-stlport_shared-exception',
    'test-stlport_static-exception',
    'test-gnustl_shared-exception-full',
    'test-gnustl_static-exception-full',
    'test-googletest-full',
    'test-libc++-shared-full',
    'test-libc++-static-full',
)


def android_platform_version(version_string):
    match = re.match(r'^android-(\d+)$', version_string)
    if not match:
        raise argparse.ArgumentTypeError(
            'Platform version must match the format "android-VERSION".')
    return int(match.group(1))


class ArgParser(argparse.ArgumentParser):
    def __init__(self):
        super(ArgParser, self).__init__(
            description=inspect.getdoc(sys.modules[__name__]))

        self.add_argument(
            'ndk', metavar='NDK', type=os.path.realpath, nargs='?',
            help='Path to NDK under test.')

        self.add_argument(
            '--abi', choices=SUPPORTED_ABIS, required=True,
            help=('Run tests against the specified ABI.'))
        self.add_argument(
            '--platform', default=None, type=android_platform_version,
            help=('Run tests against the specified platform version. Defaults '
                  'to the contents of APP_PLATFORM in jni/Application.mk'))
        self.add_argument(
            '--toolchain', default='clang', choices=('4.9', 'clang'),
            help='Toolchain for building tests. Defaults to clang.')

        self.add_argument(
            '--force-unified-headers', action='store_true',
            help='Set `APP_UNIFIED_HEADERS=true` for all builds.')

        self.add_argument(
            '--show-commands', action='store_true',
            help='Show build commands for each test.')
        self.add_argument(
            '--skip-run', action='store_true',
            help='Do not run device tests; just build them.')
        self.add_argument(
            '--suite', default=None,
            choices=('awk', 'build', 'device'),
            help=('Run only the chosen test suite.'))
        self.add_argument(
            '-v', '--verbose', action='count', default=0,
            help='Increase log level. Defaults to logging.WARNING.')

        self.add_argument(
            '--filter', help='Only run tests that match the given pattern.')
        self.add_argument(
            '--show-all', action='store_true',
            help='Show all test results, not just failures.')

        self.add_argument(
            '--out-dir',
            help='Path to build tests to. Will not be removed upon exit.')


def main():
    if sys.platform != 'win32':
        ndk.debug.register_debug_handler(signal.SIGUSR1)
        ndk.debug.register_trace_handler(signal.SIGUSR2)

    orig_cwd = os.getcwd()

    args = ArgParser().parse_args()

    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    verbosity = min(args.verbose, len(log_levels) - 1)
    log_level = log_levels[verbosity]
    logging.basicConfig(level=log_level)

    ndk_path = args.ndk
    if ndk_path is None:
        ndk_path = ndk.paths.get_install_path()

    min_platform = build.lib.build_support.minimum_platform_level(args.abi)
    if args.platform is not None and args.platform < min_platform:
        sys.exit('Unsupported platform version {} for {}. Minimum supported '
                 'version is android-{}.'.format(args.platform, args.abi,
                                                 min_platform))

    # We need to do this here rather than at the top because we load the module
    # from a path that is given on the command line. We load it from the NDK
    # given on the command line so this script can be run even without a full
    # platform checkout.
    site.addsitedir(os.path.join(ndk_path, 'python-packages'))

    import tests.printers
    import tests.runners

    out_dir = args.out_dir
    if out_dir is not None:
        if not os.path.isabs(out_dir):
            out_dir = os.path.join(orig_cwd, out_dir)
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir)
    else:
        out_dir = tempfile.mkdtemp()
        atexit.register(lambda: shutil.rmtree(out_dir))

    suites = ['awk', 'build', 'device']
    if args.suite:
        suites = [args.suite]

    use_color = sys.stdin.isatty() and os.name != 'nt'
    printer = tests.printers.StdoutPrinter(use_color=use_color,
                                           show_all=args.show_all)
    good, _ = tests.runners.run_single_configuration(
        ndk_path, out_dir, printer, args.abi, args.toolchain, args.platform,
        args.show_commands, suites=suites, test_filter=args.filter,
        skip_run=args.skip_run,
        force_unified_headers=args.force_unified_headers)

    subject = 'NDK Testing {}!'.format('Passed' if good else 'Failed')
    ndk.notify.toast(subject)

    sys.exit(not good)


if __name__ == '__main__':
    main()
