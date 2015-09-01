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
"""Verifies that the build is sane.

Cleans old build artifacts, configures the required environment, determines
build goals, and invokes the build scripts.
"""
import argparse
import datetime
import inspect
import os
import platform
import site
import subprocess
import sys

site.addsitedir(os.path.join(os.path.dirname(__file__), 'build/lib'))

import build_support


class ArgParser(argparse.ArgumentParser):
    def __init__(self):
        super(ArgParser, self).__init__(
            description=inspect.getdoc(sys.modules[__name__]))

        self.add_argument(
            '--arch',
            choices=('arm', 'arm64', 'mips', 'mips64', 'x86', 'x86_64'),
            help='Build for the given architecture. Build all by default.')

        self.add_argument(
            '--host-only', action='store_true',
            help='Skip building target components.')

        self.add_argument(
            '--skip-gcc', action='store_true',
            help='Skip building and packaging GCC.')

        self.add_argument(
            '--package', action='store_true', dest='package', default=True,
            help='Package the NDK when done building.')
        self.add_argument(
            '--no-package', action='store_false', dest='package',
            help='Do not package the NDK when done building.')

        self.add_argument(
            '--release', default=datetime.date.today().strftime('%Y%m%d'),
            help='Release name. Package will be named android-ndk-RELEASE.')

        system_group = self.add_mutually_exclusive_group()
        system_group.add_argument(
            '--system', choices=('darwin', 'linux', 'windows', 'windows64'),
            help='Build for the given OS.')

        old_choices = (
            'darwin', 'darwin-x86',
            'linux', 'linux-x86',
            'windows',
        )

        system_group.add_argument(
            '--systems', choices=old_choices, dest='system',
            help='Build for the given OS. Deprecated. Use --system instead.')


def invoke_build(script, args=None):
    if args is None:
        args = []
    subprocess.check_call([os.path.join('build/tools', script)] + args)


def build_ndk(out_dir, build_args, host_only):
    build_args = list(build_args)
    build_args.append('--package-dir={}'.format(out_dir))
    build_args.append('--verbose')

    if host_only:
        ndk_dir_arg = '--ndk-dir={}'.format(os.getcwd())
        invoke_build('build-host-prebuilts.sh',
                     build_args + [ndk_dir_arg])
    else:
        invoke_build('rebuild-all-prebuilt.sh', build_args)


def package_ndk(release_name, system, out_dir, build_args):
    package_args = [
        '--out-dir={}'.format(out_dir),
        '--prebuilt-dir={}'.format(out_dir),
        '--release={}'.format(release_name),
        '--systems={}'.format(system),
    ]
    invoke_build('package-release.sh', package_args + build_args)


def main():
    args, build_args = ArgParser().parse_known_args()

    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # Set ANDROID_BUILD_TOP.
    if 'ANDROID_BUILD_TOP' not in os.environ:
        os.environ['ANDROID_BUILD_TOP'] = os.path.realpath('..')
    build_top = os.getenv('ANDROID_BUILD_TOP')

    system = args.system
    if system != 'windows':
        build_args.append('--try-64')

    if system is not None:
        # TODO(danalbert): Update build server to pass just 'linux'.
        original_system = system
        if system == 'darwin':
            system = 'darwin-x86'
        elif system == 'linux':
            system = 'linux-x86'
        elif system == 'windows64':
            system = 'windows'

        if system not in ('darwin-x86', 'linux-x86', 'windows'):
            sys.exit('Unknown system requested: {}'.format(original_system))

        build_args.append('--systems={}'.format(system))
    else:
        # No flag provided. Use the current OS.
        if platform.system() == 'Darwin':
            system = 'darwin-x86'
        elif platform.system() == 'Linux':
            system = 'linux-x86'
        else:
            sys.exit('Unknown build host: {}'.format(platform.system()))

    build_args.append(os.path.join(build_top, 'toolchain'))

    DEFAULT_OUT_DIR = os.path.join(build_top, 'out/ndk')
    out_dir = os.path.realpath(os.getenv('DIST_DIR', DEFAULT_OUT_DIR))

    common_build_args = ['--package-dir={}'.format(out_dir)]
    if args.system is not None:
        # Need to use args.system directly rather than system because system is
        # the name used by the build/tools scripts (i.e. linux-x86 instead of
        # linux).
        common_build_args.append('--host={}'.format(args.system))

    gcc_build_args = list(common_build_args)
    gdb_build_args = list(common_build_args)
    if args.arch is not None:
        build_args.append('--arch={}'.format(args.arch))

        toolchain_name = build_support.arch_to_toolchain(args.arch)
        gcc_build_args.append('--toolchain={}'.format(toolchain_name))

        gdb_build_args.append('--arch={}'.format(args.arch))

    invoke_build('dev-cleanup.sh')
    if not args.skip_gcc:
        invoke_build('../../../toolchain/gcc/build.py', gcc_build_args)

    invoke_build('../../../toolchain/python/build.py', common_build_args)
    invoke_build('../../../toolchain/gdb/build.py', gdb_build_args)
    invoke_build('../../../toolchain/yasm/build.py', common_build_args)

    build_ndk(out_dir, build_args, host_only=args.host_only)

    if args.package and not args.host_only:
        package_ndk(args.release, system, out_dir, build_args)


if __name__ == '__main__':
    main()
