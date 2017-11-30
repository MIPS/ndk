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
"""Constants and helper functions for NDK hosts."""
from __future__ import absolute_import

import os
import sys


def get_host_tag(ndk_path):
    if sys.platform.startswith('linux'):
        return 'linux-x86_64'
    elif sys.platform == 'darwin':
        return 'darwin-x86_64'
    elif sys.platform == 'win32':
        host_tag = 'windows-x86_64'
        test_path = os.path.join(ndk_path, 'prebuilt', host_tag)
        if not os.path.exists(test_path):
            host_tag = 'windows'
        return host_tag


def host_to_tag(host):
    if host in ['darwin', 'linux']:
        return host + '-x86_64'
    elif host == 'windows':
        return 'windows'
    elif host == 'windows64':
        return 'windows-x86_64'
    else:
        raise RuntimeError('Unsupported host: {}'.format(host))


def get_default_host():
    if sys.platform in ('linux', 'linux2'):
        return 'linux'
    elif sys.platform == 'darwin':
        return 'darwin'
    elif sys.platform == 'win32':
        return 'windows'
    else:
        raise RuntimeError('Unsupported host: {}'.format(sys.platform))
