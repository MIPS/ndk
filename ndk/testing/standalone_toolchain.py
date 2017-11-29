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

import ndk.abis


def logger():
    return logging.getLogger(__name__)


def call_output(cmd, *args, **kwargs):
    logger().info('COMMAND: ' + ' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, *args, **kwargs)
    out, _ = proc.communicate()
    return proc.returncode, out


def make_standalone_toolchain(ndk_path, arch, api, extra_args, install_dir):
    make_standalone_toolchain_path = os.path.join(
        ndk_path, 'build/tools/make_standalone_toolchain.py')

    cmd = [make_standalone_toolchain_path, '--force',
           '--install-dir=' + install_dir, '--arch=' + arch,
           '--api={}'.format(api)] + extra_args

    if os.name == 'nt':
        # Windows doesn't process shebang lines, and we wouldn't be pointing at
        # the right Python if it did. Explicitly invoke the NDK's Python for on
        # Windows.
        prebuilt_dir = os.path.join(ndk_path, 'prebuilt/windows-x86_64')
        if not os.path.exists(prebuilt_dir):
            prebuilt_dir = os.path.join(ndk_path, 'prebuilt/windows')
        if not os.path.exists(prebuilt_dir):
            raise RuntimeError('Could not find prebuilts in {}'.format(
                os.path.join(ndk_path, 'prebuilt')))

        python_path = os.path.join(prebuilt_dir, 'bin/python.exe')
        cmd = [python_path] + cmd

    rc, out = call_output(cmd)
    return rc == 0, out


def test_standalone_toolchain(arch, toolchain, install_dir, test_source,
                              flags):
    if toolchain == '4.9':
        triple = ndk.abis.arch_to_triple(arch)
        # x86 toolchain names are dumb: http://b/25800583
        if arch == 'x86':
            triple = 'i686-linux-android'
        elif arch == 'arm':
            # This is added by default for Clang, but we don't wrap the GCC
            # compilers.
            flags.append('-march=armv7-a')
        compiler_name = triple + '-g++'
    elif toolchain == 'clang':
        compiler_name = 'clang++'

    compiler = os.path.join(install_dir, 'bin', compiler_name)
    cmd = [compiler, test_source, '-Wl,--no-undefined', '-Wl,--fatal-warnings']
    cmd += flags
    if os.name == 'nt':
        # The Windows equivalent of exec doesn't know file associations so it
        # tries to load the batch file as an executable. Invoke it with cmd.
        cmd = ['cmd', '/c'] + cmd
    rc, out = call_output(cmd)
    return rc == 0, out


def run_test(ndk_path, abi, api, toolchain, test_source, extra_args, flags):
    arch = ndk.abis.abi_to_arch(abi)

    install_dir = tempfile.mkdtemp()
    try:
        success, out = make_standalone_toolchain(
            ndk_path, arch, api, extra_args, install_dir)
        if not success:
            return success, out
        return test_standalone_toolchain(
            arch, toolchain, install_dir, test_source, flags)
    finally:
        shutil.rmtree(install_dir)
