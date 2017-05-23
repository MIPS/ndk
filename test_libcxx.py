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
"""Runs the libc++ test suite."""
import argparse
import os
import shutil
import site
import subprocess

import build.lib.build_support
import ndk.paths


def prep_device(device, libcxx_dir, device_dir, abi):
    device.shell_nocheck(['rm', '-r', device_dir])
    device.shell(['mkdir', device_dir])
    libcxx_lib = os.path.join(libcxx_dir, 'libs', abi, 'libc++_shared.so')
    device.push(libcxx_lib, device_dir)


def find_host_tag(ndk_path):
    dirs = os.listdir(os.path.join(ndk_path, 'toolchains/llvm/prebuilt'))
    if len(dirs) != 1:
        raise RuntimeError('Found multiple toolchain hosts.')
    return dirs[0]


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-a', '--abi', required=True, choices=build.lib.build_support.ALL_ABIS,
        help='ABI to test.')
    parser.add_argument(
        '-p', '--platform', required=True, type=int,
        help='API level to build against.')
    parser.add_argument(
        '--deprecated-headers', action='store_true', default=False,
        help='Use NDK deprecated headers.')
    parser.add_argument(
        '--pie', action='store_true', default=False,
        help='Force building with PIE.')
    parser.add_argument(
        '-t', '--timeout', default=300, type=int,
        help='Per-test timeout in seconds.')
    parser.add_argument(
        '--build-only', action='store_true',
        help='Build tests only. Skip run and do not use adb.')

    parser.add_argument(
        '--out-dir', type=os.path.realpath, help='Build output directory.')

    parser.add_argument(
        '--ndk', type=os.path.realpath, help='Path to NDK under test.')

    return parser.parse_known_args()


def main():
    args, extra_args = parse_args()

    if args.ndk is None:
        args.ndk = ndk.paths.get_install_path()

    libcxx_dir = os.path.join(args.ndk, 'sources/cxx-stl/llvm-libc++')
    device_dir = '/data/local/tmp/libcxx'
    if not args.build_only:
        # We need to do this here rather than at the top because we load the
        # module from a path that is given on the command line. We load it from
        # the NDK given on the command line so this script can be run even
        # without a full platform checkout.
        site.addsitedir(os.path.join(args.ndk, 'python-packages'))
        import adb  # pylint: disable=import-error
        device = adb.get_device()
        prep_device(device, libcxx_dir, device_dir, args.abi)

    arch = build.lib.build_support.abi_to_arch(args.abi)
    host_tag = find_host_tag(args.ndk)
    triple = build.lib.build_support.arch_to_triple(arch)
    toolchain = build.lib.build_support.arch_to_toolchain(arch)

    lit_path = build.lib.build_support.android_path(
        'external/llvm/utils/lit/lit.py')

    replacements = [
        ('abi', args.abi),
        ('api', args.platform),
        ('arch', arch),
        ('host_tag', host_tag),
        ('toolchain', toolchain),
        ('triple', triple),
        ('use_pie', args.pie),
        ('build_dir', args.out_dir),
    ]
    lit_cfg_args = []
    for key, value in replacements:
        lit_cfg_args.append('--param={}={}'.format(key, value))

    shutil.copy2(os.path.join(libcxx_dir, 'test/lit.ndk.cfg.in'),
                 os.path.join(libcxx_dir, 'test/lit.site.cfg'))

    default_test_path = os.path.join(libcxx_dir, 'test')
    have_filter_args = False
    for arg in extra_args:
        # If the argument is a valid path with default_test_path, it is a
        # test filter.
        real_path = os.path.realpath(arg)
        if not real_path.startswith(default_test_path):
            continue
        if not os.path.exists(real_path):
            continue

        have_filter_args = True
        break  # No need to keep scanning.

    lit_args = [
        lit_path, '-sv', '--param=device_dir=' + device_dir,
        '--param=unified_headers={}'.format(not args.deprecated_headers),
    ] + lit_cfg_args + extra_args

    if args.build_only:
        lit_args.append('--param=build_only=True')
    else:
        lit_args.append('--timeout={}'.format(args.timeout))

    if not have_filter_args:
        lit_args.append(default_test_path)
    env = dict(os.environ)
    env['NDK'] = args.ndk
    subprocess.check_call(lit_args, env=env)


if __name__ == '__main__':
    main()
