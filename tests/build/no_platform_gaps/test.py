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


def build(ndk_dir, abi, platform, build_flags):
    ndk_build = os.path.join(ndk_dir, 'ndk-build')
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
    return proc.returncode == 0, out


def run_test(ndk_path, abi, _platform, _toolchain, build_flags):
    """Checks ndk-build V=1 output for correct compiler."""
    min_api = None
    max_api = None
    apis = []
    for name in os.listdir(os.path.join(ndk_path, 'platforms')):
        if not name.startswith('android-'):
            continue

        _, api_str = name.split('-')

        try:
            api = int(api_str)
        except ValueError:
            # Must have been a lettered release. Not relevant.
            continue

        apis.append(api)
        if min_api is None or api < min_api:
            min_api = api
        if max_api is None or api > max_api:
            max_api = api

    missing_platforms = sorted(list(set(range(min_api, max_api)) - set(apis)))
    for api in missing_platforms:
        result, out = build(ndk_path, abi, api, build_flags)
        if not result:
            return result, out

    return True, ''
