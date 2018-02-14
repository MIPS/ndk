#!/usr/bin/env python
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
"""NDK packaging APIs."""
from __future__ import absolute_import

import os
import shutil
import subprocess
import tempfile

import ndk.abis
import ndk.hosts


PACKAGE_VARIANTS = (
    'abi',
    'arch',
    'host',
    'toolchain',
    'triple',
)


def expand_paths(package, host, arches):
    """Expands package definition tuple into list of full package names.

    >>> expand_paths('gcc-{toolchain}-{host}', 'linux', ['arm', 'x86_64'])
    ['gcc-arm-linux-androideabi-linux-x86_64', 'gcc-x86_64-linux-x86_64']

    >>> expand_paths('gdbserver-{arch}', 'linux', ['arm64', 'x86_64'])
    ['gdbserver-arm64', 'gdbserver-x86_64']

    >>> expand_paths('llvm-{host}', 'linux', None)
    ['llvm-linux-x86_64']

    >>> expand_paths('platforms', 'linux', ['arm'])
    ['platforms']

    >>> expand_paths('libc++-{abi}', 'linux', ['arm'])
    ['libc++-armeabi-v7a']

    >>> expand_paths('binutils/{triple}', 'linux', ['arm', 'x86_64'])
    ['binutils/arm-linux-androideabi', 'binutils/x86_64-linux-android']

    >> expand_paths('toolchains/{toolchain}-4.9', 'linux', ['arm', 'x86'])
    ['toolchains/arm-linux-androideabi-4.9', 'toolchains/x86-4.9']
    """
    host_tag = ndk.hosts.host_to_tag(host)
    if arches is None:
        return [package.format(host=host_tag)]

    seen_packages = set()
    packages = []
    for arch in arches:
        triple = ndk.abis.arch_to_triple(arch)
        toolchain = ndk.abis.arch_to_toolchain(arch)
        for abi in ndk.abis.arch_to_abis(arch):
            expanded = package.format(
                abi=abi, arch=arch, host=host_tag, triple=triple,
                toolchain=toolchain)
            if expanded not in seen_packages:
                packages.append(expanded)
            seen_packages.add(expanded)
    return packages


def package_varies_by(install_path, variant):
    """Determines if a package varies by a given input.

    >>> package_varies_by('foo-{host}', 'host')
    True

    >>> package_varies_by('foo', 'host')
    False

    >>> package_varies_by('foo-{arch}', 'host')
    False
    """

    if variant not in PACKAGE_VARIANTS:
        raise ValueError

    variant_replacement_str = '{' + variant + '}'
    return variant_replacement_str in install_path


def expand_packages(package, install_path, host, arches):
    """Returns a list of tuples of `(package, install_path)`."""
    package_template = package
    for variant in PACKAGE_VARIANTS:
        if package_varies_by(install_path, variant):
            package_template += '-{' + variant + '}'

    expanded_packages = expand_paths(package_template, host, arches)
    expanded_installs = expand_paths(install_path, host, arches)
    return zip(expanded_packages, expanded_installs)


def extract_zip(package_path, install_path):
    """Extracts the contents of a zipfile to a directory.

    This behaves similar to the following shell commands (using tar instead of
    zip because `unzip` doesn't support `--strip-components`):

        mkdir -p $install_path
        tar xf $package_path -C $install_path --strip-components=1

    That is, the first directory in the package is stripped and the contents
    are placed in the install path.

    Args:
        package_path: Path to the zip file to extract.
        install_path: Directory in which to extract zip contents.

    Raises:
        RuntimeError: The zip file was not in the allowed format. i.e. the zip
                      had more than one top level directory or was empty.
    """
    package_name = os.path.basename(package_path)
    extract_dir = tempfile.mkdtemp()
    try:
        subprocess.check_call(
            ['unzip', '-q', package_path, '-d', extract_dir])
        dirs = os.listdir(extract_dir)
        if len(dirs) > 1:
            msg = 'Package has more than one root directory: ' + package_name
            raise RuntimeError(msg)
        elif len(dirs) == 0:
            raise RuntimeError('Package was empty: ' + package_name)
        parent_dir = os.path.dirname(install_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        shutil.move(os.path.join(extract_dir, dirs[0]), install_path)
    finally:
        shutil.rmtree(extract_dir)
