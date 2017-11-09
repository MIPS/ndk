#
# Copyright (C) 2017 The Android Open Source Project
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
"""Setup module for the NDK build and test tools."""
from __future__ import absolute_import

import os
import setuptools


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


with open(os.path.join(THIS_DIR, 'README.md')) as readme_file:
    LONG_DESCRIPTION = readme_file.read()


setuptools.setup(
    name='ndk',
    version='1.0.0',

    description='Build and test tools for working on the NDK.',
    long_description=LONG_DESCRIPTION,

    packages=setuptools.find_packages(),

    entry_points={
        'console_scripts': [
            'run_tests.py = ndk.run_tests:main',
        ],
    },
)
