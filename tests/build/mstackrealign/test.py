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
"""Check for mstackrealign use for old x86 targets.

http://b.android.com/222239 reports that old x86 targets have stack alignment
issues. For these devices, verify that mstackrealign is used.
"""
import os
import subprocess
import sys


def run_test(ndk_path, abi, platform, toolchain, build_flags):
    """Checks ndk-build V=1 output for mstackrealign flag."""
    ndk_build = os.path.join(ndk_path, 'ndk-build')
    if sys.platform == 'win32':
        ndk_build += '.cmd'
    project_path = 'project'
    ndk_args = build_flags + [
        'APP_ABI=' + abi,
        'APP_PLATFORM=android-{}'.format(platform),
        'NDK_TOOLCHAIN_VERSION=' + toolchain,
        'V=1',
    ]
    proc = subprocess.Popen([ndk_build, '-C', project_path] + ndk_args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = proc.communicate()
    if proc.returncode != 0:
        return proc.returncode == 0, out

    out_words = out.split(' ')
    if abi == 'x86':
        result = '-mstackrealign' in out_words
    else:
        result = '-mstackrealign' not in out_words

    return result, out
