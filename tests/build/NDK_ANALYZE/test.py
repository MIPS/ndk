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
import os
import subprocess


def run_test(abi, platform, _toolchain, build_flags):
    """Runs the static analyzer on a sample project."""
    ndk_dir = os.environ['NDK']
    ndk_build = os.path.join(ndk_dir, 'ndk-build')
    project_path = 'project'
    analyzer_out = os.path.join(project_path, 'report')
    ndk_args = build_flags + [
        'APP_ABI=' + abi,
        'APP_PLATFORM=android-{}'.format(platform),
        'NDK_ANALYZE=1',
        'NDK_ANALYZER_OUT=' + analyzer_out,
    ]
    proc = subprocess.Popen([ndk_build, '-C', project_path] + ndk_args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = proc.communicate()
    # We expect the analyzer to find an issue and exit with a failure.
    if proc.returncode == 0:
        return False, out

    analyzer_abi_out = os.path.join(analyzer_out, abi)
    # The out directory gets created even if the analyzer fails, so we
    # intentionally include bad code and make sure we get a failure report.
    reports = os.listdir(analyzer_abi_out)
    if len(reports) == 0:
        return False, 'No analyzer output found in ' + analyzer_abi_out

    return True, out
