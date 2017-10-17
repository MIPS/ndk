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
"""Checks that Application.mk values are obeyed.

http://b.android.com/230228 reports that r14-beta1 stopped obeying
Application.mk settigns for NDK_TOOLCHAIN_VERSION. The cause of this was
https://android-review.googlesource.com/c/303887/. None of our tests caught
this because our test runner passes the toolchain to tests as a command line
argument, which *is* obeyed.

This test is a Python driven test specifically to avoid the test runner's
meddling.
"""
import os
import subprocess
import sys


def run_test(ndk_path, abi, platform, _toolchain, build_flags):
    """Checks ndk-build V=1 output for correct compiler."""
    ndk_build = os.path.join(ndk_path, 'ndk-build')
    if sys.platform == 'win32':
        ndk_build += '.cmd'
    project_path = 'project'
    ndk_args = build_flags + [
        'APP_ABI=' + abi,
        'APP_PLATFORM=android-{}'.format(platform),
        'V=1',
    ]
    proc = subprocess.Popen([ndk_build, '-C', project_path] + ndk_args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = proc.communicate()
    if proc.returncode != 0:
        return proc.returncode == 0, out

    result = False
    for line in out.splitlines():
        words = line.split()
        if '-o' not in words:
            continue

        compiler = os.path.basename(words[0])
        result = not compiler.endswith('clang++')
        break
    return result, out
