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
"""Constants and helper functions for NDK ABIs."""


LP32_ABIS = (
    'armeabi',
    'armeabi-v7a',
    'mips',
    'x86',
)


LP64_ABIS = (
    'arm64-v8a',
    'mips64',
    'x86_64',
)


def min_api_for_abi(abi):
    """Returns the minimum supported build API for the given ABI.

    >>> min_api_for_abi('arm64-v8a')
    21

    >>> min_api_for_abi('armeabi-v7a')
    14

    >>> min_api_for_abi('foobar')
    Traceback (most recent call last):
        ...
    ValueError: Invalid ABI: foobar
    """
    if abi in LP64_ABIS:
        return 21
    elif abi in LP32_ABIS:
        return 14
    else:
        raise ValueError('Invalid ABI: {}'.format(abi))
