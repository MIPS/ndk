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
    'armeabi-v7a',
    'mips',
    'x86',
)


LP64_ABIS = (
    'arm64-v8a',
    'mips64',
    'x86_64',
)


ALL_ABIS = sorted(LP32_ABIS + LP64_ABIS)


ALL_ARCHITECTURES = (
    'arm',
    'arm64',
    'mips',
    'mips64',
    'x86',
    'x86_64',
)


ALL_TOOLCHAINS = (
    'arm-linux-androideabi',
    'aarch64-linux-android',
    'mipsel-linux-android',
    'mips64el-linux-android',
    'x86',
    'x86_64',
)


ALL_TRIPLES = (
    'arm-linux-androideabi',
    'aarch64-linux-android',
    'mipsel-linux-android',
    'mips64el-linux-android',
    'i686-linux-android',
    'x86_64-linux-android',
)


def arch_to_toolchain(arch):
    return dict(zip(ALL_ARCHITECTURES, ALL_TOOLCHAINS))[arch]


def arch_to_triple(arch):
    return dict(zip(ALL_ARCHITECTURES, ALL_TRIPLES))[arch]


def toolchain_to_arch(toolchain):
    return dict(zip(ALL_TOOLCHAINS, ALL_ARCHITECTURES))[toolchain]


def arch_to_abis(arch):
    return {
        'arm': ['armeabi-v7a'],
        'arm64': ['arm64-v8a'],
        'mips': ['mips'],
        'mips64': ['mips64'],
        'x86': ['x86'],
        'x86_64': ['x86_64'],
    }[arch]


def abi_to_arch(arch):
    return {
        'armeabi-v7a': 'arm',
        'arm64-v8a': 'arm64',
        'mips': 'mips',
        'mips64': 'mips64',
        'x86': 'x86',
        'x86_64': 'x86_64',
    }[arch]


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
