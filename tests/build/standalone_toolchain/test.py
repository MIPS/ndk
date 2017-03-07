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
import logging
import os
import shutil
import subprocess
import tempfile

import build.lib.build_support


def logger():
    return logging.getLogger(__name__)


def call_output(cmd, *args, **kwargs):
    logger().info('COMMAND: ' + ' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, *args, **kwargs)
    out, _ = proc.communicate()
    return proc.returncode, out


def make_standalone_toolchain(arch, api, install_dir):
    ndk_dir = os.environ['NDK']
    make_standalone_toolchain_path = os.path.join(
        ndk_dir, 'build/tools/make_standalone_toolchain.py')

    cmd = [make_standalone_toolchain_path, '--force',
           '--install-dir=' + install_dir, '--arch=' + arch,
           '--api={}'.format(api), '--stl=libc++']

    rc, out = call_output(cmd)
    return rc == 0, out


def test_standalone_toolchain(arch, toolchain, install_dir):
    if toolchain == '4.9':
        triple = build.lib.build_support.arch_to_triple(arch)
        # x86 toolchain names are dumb: http://b/25800583
        if arch == 'x86':
            triple = 'i686-linux-android'
        compiler_name = triple + '-g++'
    elif toolchain == 'clang':
        compiler_name = 'clang++'

    compiler = os.path.join(install_dir, 'bin', compiler_name)
    test_source = 'foo.cpp'
    cmd = [compiler, test_source, '-Wl,--no-undefined', '-Wl,--fatal-warnings']
    rc, out = call_output(cmd)
    return rc == 0, out


def run_test(abi, platform, toolchain, _build_flags):
    arch = build.lib.build_support.abi_to_arch(abi)

    install_dir = tempfile.mkdtemp()
    try:
        success, out = make_standalone_toolchain(arch, platform, install_dir)
        if not success:
            return success, out
        return test_standalone_toolchain(arch, toolchain, install_dir)
    finally:
        shutil.rmtree(install_dir)
