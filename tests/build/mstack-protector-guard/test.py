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
"""Check for mstack-protector-guard=global when targeting old x86 targets.

https://gcc.gnu.org/ml/gcc/2015-11/msg00060.html changed the default for this
from using a global to using the TLS slot. As noted in
https://github.com/android-ndk/ndk/issues/297 (and in that commit), this is not
compatible with pre-4.2 devices, so we need to guard against that in the NDK.
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

    search_text = '-mstack-protector-guard=global'
    out_words = out.split(' ')
    if abi == 'x86' and platform < 17 and toolchain == '4.9':
        if search_text in out_words:
            return True, out
        else:
            out = 'Did not find {} in output:\n{}'.format(search_text, out)
            return False, out
    else:
        if search_text in out_words:
            print 'Found unexpceted {} in output:\n'.format(search_text, out)
            return False, out
        else:
            return True, out
