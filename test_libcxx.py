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
import site
import subprocess

import build.lib.build_support


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-a', '--abi', required=True, choices=build.lib.build_support.ALL_ABIS,
        help='ABI to test.')
    parser.add_argument(
        '-p', '--platform', required=True, type=int,
        help='API level to build against.')
    parser.add_argument(
        '--unified-headers', action='store_true', default=False,
        help='Use NDK unified headers.')
    parser.add_argument(
        '-t', '--timeout', default=300, type=int,
        help='Per-test timeout in seconds.')

    parser.add_argument(
        'ndk', metavar='NDK', type=os.path.realpath,
        help='Path to NDK under test.')

    return parser.parse_known_args()


def main():
    args, extra_args = parse_args()

    # We need to do this here rather than at the top because we load the module
    # from a path that is given on the command line. We load it from the NDK
    # given on the command line so this script can be run even without a full
    # platform checkout.
    site.addsitedir(os.path.join(args.ndk, 'python-packages'))
    import adb  # pylint: disable=import-error
    device = adb.get_device()

    arch = build.lib.build_support.abi_to_arch(args.abi)
    triple = build.lib.build_support.arch_to_triple(arch)
    toolchain = build.lib.build_support.arch_to_toolchain(arch)

    lit_path = build.lib.build_support.android_path(
        'external/llvm/utils/lit/lit.py')
    libcxx_dir = os.path.join(args.ndk, 'sources/cxx-stl/llvm-libc++')

    device_api_level = device.get_prop('ro.build.version.sdk')

    replacements = [
        ('ABI', args.abi),
        ('API', args.platform),
        ('ARCH', arch),
        ('DEVICE_API', device_api_level),
        ('TOOLCHAIN', toolchain),
        ('TRIPLE', triple),
    ]
    sed_args = ['sed']
    for key, repl in replacements:
        sed_args.extend(['-e', 's:%{}%:{}:g'.format(key, repl)])
    sed_args.append(os.path.join(libcxx_dir, 'test/lit.ndk.cfg.in'))
    with open(os.path.join(libcxx_dir, 'test/lit.site.cfg'), 'w') as cfg_file:
        subprocess.check_call(sed_args, stdout=cfg_file)

    device_dir = '/data/local/tmp/libcxx'
    device.shell_nocheck(['rm', '-r', device_dir])
    device.shell(['mkdir', device_dir])
    libcxx_lib = os.path.join(libcxx_dir, 'libs', args.abi, 'libc++_shared.so')
    device.push(libcxx_lib, device_dir)

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
        '--param=unified_headers={}'.format(args.unified_headers),
        '--timeout={}'.format(args.timeout)
    ] + extra_args
    if not have_filter_args:
        lit_args.append(default_test_path)
    env = dict(os.environ)
    env['NDK'] = args.ndk
    subprocess.check_call(lit_args, env=env)


if __name__ == '__main__':
    main()
