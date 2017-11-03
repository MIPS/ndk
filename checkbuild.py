#!/usr/bin/env python
#
# Copyright (C) 2015 The Android Open Source Project
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
"""Verifies that the build is sane.

Cleans old build artifacts, configures the required environment, determines
build goals, and invokes the build scripts.
"""
from __future__ import absolute_import
from __future__ import print_function

import argparse
import copy
import distutils.spawn
import errno
import inspect
import json
import logging
import multiprocessing
import os
import shutil
import site
import subprocess
import sys
import tempfile
import textwrap
import traceback

import config
import build.lib.build_support as build_support
import ndk.ansi
import ndk.builds
import ndk.notify
import ndk.paths
import ndk.test.builder
import ndk.test.spec
import ndk.timer
import ndk.ui
import ndk.workqueue

import tests.printers

from ndk.builds import common_build_args, invoke_build, invoke_external_build


def _make_tar_package(package_path, base_dir, path):
    """Creates a tarball package for distribution.

    Args:
        package_path (string): Path (without extention) to the output archive.
        base_dir (string): Path to the directory from which to perform the
                           packaging (identical to tar's -C).
        path (string): Path to the directory to package.
    """
    has_pbzip2 = distutils.spawn.find_executable('pbzip2') is not None
    if has_pbzip2:
        compress_arg = '--use-compress-prog=pbzip2'
    else:
        compress_arg = '-j'

    cmd = ['tar', compress_arg, '-cf',
           package_path + '.tar.bz2', '-C', base_dir, path]
    subprocess.check_call(cmd)


def _make_zip_package(package_path, base_dir, path):
    """Creates a zip package for distribution.

    Args:
        package_path (string): Path (without extention) to the output archive.
        base_dir (string): Path to the directory from which to perform the
                           packaging (identical to tar's -C).
        path (string): Path to the directory to package.
    """
    cwd = os.getcwd()
    package_path = os.path.realpath(package_path)
    os.chdir(base_dir)
    try:
        subprocess.check_call(['zip', '-9qr', package_path + '.zip', path])
    finally:
        os.chdir(cwd)


def package_ndk(ndk_dir, dist_dir, host_tag, build_number):
    """Packages the built NDK for distribution.

    Args:
        ndk_dir (string): Path to the built NDK.
        dist_dir (string): Path to place the built package in.
        host_tag (string): Host tag to use in the package name,
        build_number (printable): Build number to use in the package name. Will
                                  be 'dev' if the argument evaluates to False.
    """
    package_name = 'android-ndk-{}-{}'.format(build_number, host_tag)
    package_path = os.path.join(dist_dir, package_name)

    base_dir = os.path.dirname(ndk_dir)
    files = os.path.basename(ndk_dir)
    if host_tag.startswith('windows'):
        _make_zip_package(package_path, base_dir, files)
    else:
        _make_tar_package(package_path, base_dir, files)


def group_by_test(reports):
    """Arranges per-ABI test results into failures by name.

    Args:
        details: dict of {config_str: ndk.test.Report}.

    Returns:
        Dict of {test_name: (config_str, result)}.
    """
    by_test = {}
    for config_str, report in reports.iteritems():
        for suite, suite_report in report.by_suite().items():
            for report in suite_report.all_failed:
                name = '.'.join([suite, report.result.test.name])
                if name not in by_test:
                    by_test[name] = []
                by_test[name].append((config_str, report.result))
    return by_test


def make_test_report(reports, use_color):
    """Returns a string containing a test failure report.

    Args:
        details: dict of {config_str: ndk.test.Report}.
        use_color: Print results with color if True.

    Returns:
        Test failure report as a string.
    """
    grouped_details = group_by_test(reports)
    lines = []
    for test_name, test_failures in grouped_details.iteritems():
        lines.append('BEGIN TEST RESULT: ' + test_name)
        lines.append('=' * 80)
        for abi, result in test_failures:
            lines.append('FAILED {}'.format(abi))
            lines.append(result.to_string(colored=use_color))
    return os.linesep.join(lines)


def build_ndk_tests(out_dir, dist_dir, args):
    """Builds the NDK tests.

    Args:
        out_dir: Build output directory.
        dist_dir: Preserved artifact directory.
        args: Parsed command line arguments.

    Returns:
        True if all tests pass, else False.
    """
    # The packaging step extracts all the modules to a known directory for
    # packaging. This directory is not cleaned up after packaging, so we can
    # reuse that for testing.
    ndk_dir = ndk.paths.get_install_path(out_dir)
    test_out_dir = os.path.join(out_dir, 'tests')

    site.addsitedir(os.path.join(ndk_dir, 'python-packages'))

    test_options = ndk.test.spec.TestOptions(
       ndk_dir, test_out_dir, verbose_build=True, skip_run=True, clean=True)

    printer = tests.printers.StdoutPrinter()
    with open(os.path.realpath('qa_config.json')) as config_file:
        test_config = json.load(config_file)

    if args.arch is not None:
        test_config['abis'] = build_support.arch_to_abis(args.arch)

    test_spec = ndk.test.builder.test_spec_from_config(test_config)
    builder = ndk.test.builder.TestBuilder(
        test_spec, test_options, printer)

    report = builder.build()
    printer.print_summary(report)

    if report.successful:
        print('Packaging tests...')
        package_path = os.path.join(dist_dir, 'ndk-tests')
        _make_tar_package(package_path, out_dir, 'tests/dist')
    else:
        # Write out the result to logs/build_error.log so we can find the
        # failure easily on the build server.
        log_path = os.path.join(dist_dir, 'logs/build_error.log')
        with open(log_path, 'a') as error_log:
            error_log_printer = tests.printers.FilePrinter(error_log)
            error_log_printer.print_summary(report)

    return report.successful


def install_file(file_name, src_dir, dst_dir):
    src_file = os.path.join(src_dir, file_name)
    dst_file = os.path.join(dst_dir, file_name)

    print('Copying {} to {}...'.format(src_file, dst_file))
    if os.path.isdir(src_file):
        _install_dir(src_file, dst_file)
    elif os.path.islink(src_file):
        _install_symlink(src_file, dst_file)
    else:
        _install_file(src_file, dst_file)


def _install_dir(src_dir, dst_dir):
    parent_dir = os.path.normpath(os.path.join(dst_dir, '..'))
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    shutil.copytree(src_dir, dst_dir, symlinks=True)


def _install_symlink(src_file, dst_file):
    dirname = os.path.dirname(dst_file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    link_target = os.readlink(src_file)
    os.symlink(link_target, dst_file)


def _install_file(src_file, dst_file):
    dirname = os.path.dirname(dst_file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    # copy2 is just copy followed by copystat (preserves file metadata).
    shutil.copy2(src_file, dst_file)


class Clang(ndk.builds.Module):
    name = 'clang'
    path = 'toolchains/llvm/prebuilt/{host}'
    version = 'clang-4053586'

    def get_prebuilt_path(self, host):
        # The 32-bit Windows Clang is a part of the 64-bit Clang package in
        # prebuilts/clang.
        platform_host_tag = host + '-x86'
        if platform_host_tag.startswith('windows'):
            platform_host_tag = 'windows-x86'

        rel_prebuilt_path = 'prebuilts/clang/host/{}'.format(platform_host_tag)
        prebuilt_path = os.path.join(build_support.android_path(),
                                     rel_prebuilt_path, self.version)
        if not os.path.isdir(prebuilt_path):
            raise RuntimeError(
                'Could not find prebuilt LLVM at {}'.format(prebuilt_path))
        return prebuilt_path

    def build(self, _build_dir, _dist_dir, _args):
        pass

    def install(self, out_dir, _dist_dir, args):
        prebuilt_path = self.get_prebuilt_path(args.system)
        install_path = self.get_install_path(out_dir, args.system)

        install_parent = os.path.dirname(install_path)
        if os.path.exists(install_path):
            shutil.rmtree(install_path)
        if not os.path.exists(install_parent):
            os.makedirs(install_parent)
        shutil.copytree(prebuilt_path, install_path)

        if args.system == 'windows':
            # We need to replace clang.exe with clang_32.exe and
            # libwinpthread-1.dll with libwinpthread-1.dll.32.
            os.rename(os.path.join(install_path, 'bin/clang_32.exe'),
                      os.path.join(install_path, 'bin/clang.exe'))
            os.rename(os.path.join(install_path, 'bin/libwinpthread-1.dll.32'),
                      os.path.join(install_path, 'bin/libwinpthread-1.dll'))

            # clang++.exe is not a symlink in the Windows package. Need to copy
            # to there as well.
            shutil.copy2(os.path.join(install_path, 'bin/clang.exe'),
                         os.path.join(install_path, 'bin/clang++.exe'))
        elif args.system in ('darwin', 'linux'):
            # The Linux and Darwin toolchains have Python compiler wrappers
            # that currently do nothing. We don't have these for Windows and we
            # want to make sure Windows behavior is consistent with the other
            # platforms, so just unwrap the compilers until they do something
            # useful and are available on Windows.
            os.rename(os.path.join(install_path, 'bin/clang.real'),
                      os.path.join(install_path, 'bin/clang'))
            os.rename(os.path.join(install_path, 'bin/clang++.real'),
                      os.path.join(install_path, 'bin/clang++'))

        if args.system == 'darwin':
            # The Clang driver is dumb and looks for LLVMgold.so regardless of
            # platform.
            libs_path = os.path.join(install_path, 'lib64')
            os.rename(os.path.join(libs_path, 'LLVMgold.dylib'),
                      os.path.join(libs_path, 'LLVMgold.so'))

            # We don't build target binaries as part of the Darwin build. The
            # Darwin toolchains need to get these from the Linux prebuilts.
            #
            # The headers and libraries we care about are all in lib64/clang
            # for both toolchains, and those two are intended to be identical
            # between each host, so we can just replace Darwin's with the one
            # from the Linux toolchain.
            linux_prebuilt_path = self.get_prebuilt_path('linux')

            clanglib_dir = 'lib64/clang'
            install_clanglib = os.path.join(install_path, clanglib_dir)
            linux_clanglib = os.path.join(linux_prebuilt_path, clanglib_dir)
            shutil.rmtree(install_clanglib)
            shutil.copytree(linux_clanglib, install_clanglib)


def get_gcc_prebuilt_path(host):
    rel_prebuilt_path = 'prebuilts/ndk/current/toolchains/{}'.format(host)
    prebuilt_path = build_support.android_path(rel_prebuilt_path)
    if not os.path.isdir(prebuilt_path):
        raise RuntimeError(
            'Could not find prebuilt GCC at {}'.format(prebuilt_path))
    return prebuilt_path


class Gcc(ndk.builds.Module):
    name = 'gcc'
    path = 'toolchains/{toolchain}-4.9/prebuilt/{host}'

    def build(self, _build_dir, _dist_dir, _args):
        pass

    def install(self, out_dir, _dist_dir, args):
        arches = build_support.ALL_ARCHITECTURES
        if args.arch is not None:
            arches = [args.arch]

        for arch in arches:
            self.install_arch(out_dir, args.system, arch)

    def install_arch(self, out_dir, host, arch):
        version = '4.9'
        toolchain = build_support.arch_to_toolchain(arch)
        host_tag = build_support.host_to_tag(host)

        install_path = self.get_install_path(out_dir, host, arch)

        toolchain_name = toolchain + '-' + version
        prebuilt_path = get_gcc_prebuilt_path(host_tag)
        toolchain_path = os.path.join(prebuilt_path, toolchain_name)

        ndk.builds.install_directory(toolchain_path, install_path)

        if not host.startswith('windows'):
            so = '.so'
            if host == 'darwin':
                so = '.dylib'

            clang_libs = build_support.android_path(
                'prebuilts/ndk/current/toolchains', host_tag, 'llvm/lib64')
            llvmgold = os.path.join(clang_libs, 'LLVMgold' + so)
            libcxx = os.path.join(clang_libs, 'libc++' + so)
            libllvm = os.path.join(clang_libs, 'libLLVM' + so)

            bfd_plugins = os.path.join(install_path, 'lib/bfd-plugins')
            os.makedirs(bfd_plugins)
            shutil.copy2(llvmgold, bfd_plugins)

            # The rpath on LLVMgold.so is ../lib64, so we have to install to
            # lib/lib64 to have it be in the right place :(
            lib_dir = os.path.join(install_path, 'lib/lib64')
            os.makedirs(lib_dir)
            shutil.copy2(libcxx, lib_dir)
            shutil.copy2(libllvm, lib_dir)

        # Remove the toolchain wrappers. These don't work on Windows and we
        # don't want them anyway.
        bin_path = os.path.join(install_path, 'bin')
        triple = build_support.arch_to_triple(arch)
        for name in ('gcc', 'g++'):
            tool_name = triple + '-' + name
            real_name = 'real-' + tool_name

            # For some reason the scripts are .exe and the executables aren't.
            if host.startswith('windows'):
                tool_name += '.exe'

            tool_path = os.path.join(bin_path, tool_name)
            real_path = os.path.join(bin_path, real_name)
            os.remove(tool_path)
            os.rename(real_path, tool_path)


class ShaderTools(ndk.builds.InvokeBuildModule):
    name = 'shader-tools'
    path = 'shader-tools/{host}'
    script = 'build-shader-tools.py'


class HostTools(ndk.builds.Module):
    name = 'host-tools'
    path = 'prebuilt/{host}'

    def build(self, out_dir, dist_dir, args):
        build_args = common_build_args(out_dir, dist_dir, args)

        print('Building make...')
        invoke_external_build(
            'ndk/sources/host-tools/make-3.81/build.py', build_args)

        if args.system in ('windows', 'windows64'):
            print('Building toolbox...')
            invoke_external_build(
                'ndk/sources/host-tools/toolbox/build.py', build_args)

        print('Building Python...')
        invoke_external_build('toolchain/python/build.py', build_args)

        print('Building GDB...')
        invoke_external_build('toolchain/gdb/build.py', build_args)

        print('Building YASM...')
        invoke_external_build('toolchain/yasm/build.py', build_args)

    def install(self, out_dir, _dist_dir, args):
        install_dir = self.get_install_path(out_dir, args.system)

        try:
            os.makedirs(install_dir)
        except OSError as ex:
            # Another build might be trying to create this simultaneously,
            # which we can safely ignore.
            if ex.errno != errno.EEXIST:
                raise

        packages = [
            'gdb-multiarch-7.11',
            'ndk-make',
            'ndk-python',
            'ndk-yasm',
        ]

        files = [
            'ndk-gdb',
            'ndk-gdb.py',
            'ndk-which',
        ]

        if args.system in ('windows', 'windows64'):
            packages.append('toolbox')
            files.append('ndk-gdb.cmd')

        host_tag = build_support.host_to_tag(args.system)

        package_names = [p + '-' + host_tag + '.tar.bz2' for p in packages]
        for package_name in package_names:
            package_path = os.path.join(out_dir, package_name)
            subprocess.check_call(
                ['tar', 'xf', package_path, '-C', install_dir,
                 '--strip-components=1'])

        for f in files:
            shutil.copy2(f, os.path.join(install_dir, 'bin'))

        build_support.merge_license_files(
            os.path.join(install_dir, 'NOTICE'), [
                build_support.android_path('toolchain/gdb/gdb-7.11/COPYING'),
                build_support.ndk_path(
                    'sources/host-tools/ndk-depends/NOTICE'),
                build_support.ndk_path('sources/host-tools/make-3.81/COPYING'),
                build_support.android_path(
                    'toolchain/python/Python-2.7.5/LICENSE'),
                build_support.ndk_path('sources/host-tools/ndk-stack/NOTICE'),
                build_support.ndk_path('sources/host-tools/toolbox/NOTICE'),
                build_support.android_path('toolchain/yasm/COPYING'),
                build_support.android_path('toolchain/yasm/BSD.txt'),
                build_support.android_path('toolchain/yasm/Artistic.txt'),
                build_support.android_path('toolchain/yasm/GNU_GPL-2.0'),
                build_support.android_path('toolchain/yasm/GNU_LGPL-2.0'),
            ])

        build_support.make_repo_prop(install_dir)

        self.validate_notice(install_dir)


def install_exe(out_dir, install_dir, name, system):
    is_win = system.startswith('windows')
    ext = '.exe' if is_win else ''
    exe_name = name + ext
    src = os.path.join(out_dir, exe_name)
    dst = os.path.join(install_dir, exe_name)

    try:
        os.makedirs(install_dir)
    except OSError as ex:
        # Another build might be trying to create this simultaneously,
        # which we can safely ignore.
        if ex.errno != errno.EEXIST:
            raise

    shutil.copy2(src, dst)


class NdkDepends(ndk.builds.InvokeExternalBuildModule):
    name = 'ndk-depends'
    path = 'prebuilt/{host}/bin'
    script = 'ndk/sources/host-tools/ndk-depends/build.py'

    def install(self, out_dir, _dist_dir, args):
        src = os.path.join(out_dir, self.name)
        install_dir = self.get_install_path(out_dir, args.system)
        install_exe(src, install_dir, self.name, args.system)

    def validate_notice(self, _install_base):
        # ndk-depends shares a directory with many other components. Its
        # license is merged with the others as part of HostTools.
        pass


class NdkStack(ndk.builds.InvokeExternalBuildModule):
    name = 'ndk-stack'
    path = 'prebuilt/{host}/bin'
    script = 'ndk/sources/host-tools/ndk-stack/build.py'

    def install(self, out_dir, _dist_dir, args):
        src = os.path.join(out_dir, self.name)
        install_dir = self.get_install_path(out_dir, args.system)
        install_exe(src, install_dir, self.name, args.system)

    def validate_notice(self, _install_base):
        # ndk-stack shares a directory with many other components. Its license
        # is merged with the others as part of HostTools.
        pass


class GdbServer(ndk.builds.InvokeBuildModule):
    name = 'gdbserver'
    path = 'prebuilt/android-{arch}/gdbserver'
    script = 'build-gdbserver.py'
    arch_specific = True
    split_build_by_arch = True

    def install(self, out_dir, dist_dir, args):
        src_dir = os.path.join(out_dir, self.name, self.build_arch, 'install')
        install_path = self.get_install_path(
            out_dir, args.system, self.build_arch)
        if os.path.exists(install_path):
            shutil.rmtree(install_path)
        shutil.copytree(src_dir, install_path)

        self.validate_notice(install_path)


class Gnustl(ndk.builds.Module):
    name = 'gnustl'
    path = 'sources/cxx-stl/gnu-libstdc++/4.9'
    script = 'prebuilts/ndk/gnu-libstdc++'

    def build(self, _build_dir, _dist_dir, _args):
        pass

    def install(self, out_dir, dist_dir, args):
        src_dir = build_support.android_path('prebuilts/ndk/gnu-libstdc++')
        install_path = self.get_install_path(out_dir, args.system)
        if os.path.exists(install_path):
            shutil.rmtree(install_path)
        shutil.copytree(src_dir, install_path)

        # NDK r10 had most of gnustl installed to gnu-libstdc++/4.9, but the
        # Android.mk was one directory up from that. To remain compatible, we
        # extract the gnustl package to sources/cxx-stl/gnu-libstdc++/4.9. As
        # such, the Android.mk ends up in the 4.9 directory. We need to pull it
        # up a directory.
        os.rename(
            os.path.join(install_path, 'Android.mk'),
            os.path.join(os.path.dirname(install_path), 'Android.mk'))

        self.validate_notice(install_path)


class Libcxx(ndk.builds.InvokeExternalBuildModule):
    name = 'libc++'
    path = 'sources/cxx-stl/llvm-libc++'
    script = 'ndk/sources/cxx-stl/llvm-libc++/build.py'
    arch_specific = True


class Stlport(ndk.builds.InvokeExternalBuildModule):
    name = 'stlport'
    path = 'sources/cxx-stl/stlport'
    script = 'ndk/sources/cxx-stl/stlport/build.py'
    arch_specific = True


class Platforms(ndk.builds.Module):
    name = 'platforms'
    path = 'platforms'

    # These API levels had no new native APIs. The contents of these platforms
    # directories would be identical to the previous extant API level, so they
    # are not included in the NDK to save space.
    skip_apis = (10, 11, 20, 25)

    # We still need a numeric API level for codenamed API levels because
    # ABI_ANDROID_API in crtbrand is an integer. We start counting the
    # codenamed releases from 9000 and increment for each additional release.
    # This is filled by get_apis.
    codename_api_map = {}

    def prebuilt_path(self, *args):  # pylint: disable=no-self-use
        return build_support.android_path('prebuilts/ndk/platform', *args)

    def src_path(self, *args):  # pylint: disable=no-self-use
        return build_support.android_path('development/ndk/platforms', *args)

    def gcc_toolchain(self, arch):  # pylint: disable=no-self-use
        host_tag = build_support.host_to_tag(build_support.get_default_host())
        toolchain = build_support.arch_to_toolchain(arch) + '-4.9'
        # triple = build_support.arch_to_triple(arch)
        return build_support.android_path(
            'prebuilts/ndk/current/toolchains', host_tag, toolchain)

    def gcc_tool(self, tool, arch):
        gcc_toolchain = self.gcc_toolchain(arch)
        triple = build_support.arch_to_triple(arch)
        return os.path.join(gcc_toolchain, 'bin', triple + '-' + tool)

    def libdir_name(self, arch):  # pylint: disable=no-self-use
        if arch == 'x86_64':
            return 'lib64'
        else:
            return 'lib'

    def get_apis(self):
        codenamed_apis = []
        apis = []
        for name in os.listdir(self.prebuilt_path('platforms')):
            if not name.startswith('android-'):
                continue

            _, api_str = name.split('-')
            try:
                apis.append(int(api_str))
            except ValueError:
                # Codenamed release like android-O, android-O-MR1, etc.
                apis.append(api_str)
                codenamed_apis.append(api_str)

        for api_num, api_str in enumerate(sorted(codenamed_apis), start=9000):
            self.codename_api_map[api_str] = api_num
        return sorted(apis)

    def get_arches(self, api):  # pylint: disable=no-self-use
        arches = ['arm', 'x86']
        if api >= 21:
            arches.extend(['arm64', 'x86_64'])
        return arches

    def get_build_cmd(self, dst, srcs, api, arch, build_number):
        bionic_includes = build_support.android_path(
            'bionic/libc/arch-common/bionic')

        # TODO: Investigate crtbegin_so.o segfaults when built with Clang.
        cc = self.gcc_tool('gcc', arch)

        args = [
            cc,
            '--sysroot', self.prebuilt_path('sysroot'),
            '-I', bionic_includes,
            '-DPLATFORM_SDK_VERSION={}'.format(api),
            '-DABI_NDK_VERSION="{}"'.format(config.release),
            '-DABI_NDK_BUILD_NUMBER="{}"'.format(build_number),
            '-O2', '-fpic', '-Wl,-r', '-nostdlib', '-o', dst,
        ] + srcs

        return args

    def check_elf_note(self, obj_file):
        # readelf is a cross platform tool, so arch doesn't matter.
        readelf = self.gcc_tool('readelf', 'arm')
        out = subprocess.check_output([readelf, '--notes', obj_file])
        if 'Android' not in out:
            raise RuntimeError(
                '{} does not contain NDK ELF note'.format(obj_file))

    def build_crt_object(self, dst, srcs, api, arch, build_number, defines):
        try:
            # No-op for stable releases.
            api_num = int(api)
        except ValueError:
            # ValueError means this was a codenamed release. We need the
            # integer matching this release for ABI_ANDROID_API in crtbrand.
            api_num = self.codename_api_map[api]

        cc_args = self.get_build_cmd(dst, srcs, api_num, arch, build_number)
        cc_args.extend(defines)

        subprocess.check_call(cc_args)

    def build_crt_objects(self, dst_dir, api, arch, build_number):
        src_dir = build_support.android_path('development/ndk/crt', arch)
        sources = (
            'crtbegin.c',
            'crtbegin_so.c',
            'crtend_android.S',
            'crtend_so.S',
        )
        for src_name in sources:
            name, _ = os.path.splitext(src_name)

            is_crtbegin = name.startswith('crtbegin')
            also_static = False
            if name == 'crtbegin':
                # A single crtbegin.c is used for both crtbegin_dynamic.o and
                # crtbegin_static.o.
                name = 'crtbegin_dynamic'
                also_static = True

            dst_path = os.path.join(dst_dir, name + '.o')
            srcs = [os.path.join(src_dir, src_name)]
            if is_crtbegin:
                srcs.append(build_support.ndk_path('sources/crt/crtbrand.S'))

            defs = ['-DBUILDING_DYNAMIC'] if is_crtbegin else []
            self.build_crt_object(
                dst_path, srcs, api, arch, build_number, defs)

            if is_crtbegin:
                self.check_elf_note(dst_path)

            if also_static:
                static_dst_path = os.path.join(dst_dir, 'crtbegin_static.o')
                defs = ['-DBUILDING_STATIC']
                self.build_crt_object(
                    static_dst_path, srcs, api, arch, build_number, defs)
                self.check_elf_note(static_dst_path)

    def validate(self):
        super(Platforms, self).validate()

        first_lp32 = self.get_apis()[0]
        first_lp64 = 21
        for arch in ('arm', 'x86'):
            self.validate_src(first_lp32, arch)
        for arch in ('arm64', 'x86_64'):
            self.validate_src(first_lp64, arch)

    def validate_src(self, api, arch):
        platform = 'android-{}'.format(api)
        arch_name = 'arch-{}'.format(arch)
        lib_dir = self.src_path(platform, arch_name, self.libdir_name(arch))
        if not os.path.exists(lib_dir):
            raise self.validate_error(
                'Minimum platform API {} does not contain prebuilt static '
                'libraries ({} does not exist)'.format(api, lib_dir))

    def build(self, build_dir, _dist_dir, args):
        build_dir = os.path.join(build_dir, self.path)
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        for api in self.get_apis():
            if api in self.skip_apis:
                continue

            platform = 'android-{}'.format(api)
            for arch in self.get_arches(api):
                arch_name = 'arch-{}'.format(arch)
                dst_dir = os.path.join(build_dir, platform, arch_name)
                os.makedirs(dst_dir)
                self.build_crt_objects(dst_dir, api, arch, args.build_number)

    def install(self, out_dir, dist_dir, args):
        build_dir = os.path.join(out_dir, self.path)
        install_dir = os.path.join(
            ndk.paths.get_install_path(out_dir), self.path)

        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        os.makedirs(install_dir)

        last_platform_with_libs = None
        for api in self.get_apis():
            if api in self.skip_apis:
                continue

            # Copy shared libraries from prebuilts/ndk.
            platform = 'android-{}'.format(api)
            platform_src = self.prebuilt_path('platforms', platform)
            platform_dst = os.path.join(install_dir, 'android-{}'.format(api))
            shutil.copytree(platform_src, platform_dst)

            # Copy static libraries from development/ndk.
            for arch in self.get_arches(api):
                arch_name = 'arch-{}'.format(arch)

                libdir_name = self.libdir_name(arch)
                lib_dir = self.src_path(platform, arch_name, libdir_name)
                if os.path.exists(lib_dir):
                    last_platform_with_libs = platform
                else:
                    lib_dir = self.src_path(
                        last_platform_with_libs, arch_name, libdir_name)

                lib_dir_dst = os.path.join(
                    install_dir, platform, arch_name, 'usr', libdir_name)
                for name in os.listdir(lib_dir):
                    lib_src = os.path.join(lib_dir, name)
                    lib_dst = os.path.join(lib_dir_dst, name)
                    shutil.copy2(lib_src, lib_dst)

                if libdir_name == 'lib64':
                    # The Clang driver won't accept a sysroot that contains
                    # only a lib64. An empty lib dir is enough to convince it.
                    os.makedirs(os.path.join(
                        install_dir, platform, arch_name, 'usr/lib'))

                obj_dir = os.path.join(build_dir, platform, arch_name)
                for name in os.listdir(obj_dir):
                    obj_src = os.path.join(obj_dir, name)
                    obj_dst = os.path.join(lib_dir_dst, name)
                    shutil.copy2(obj_src, obj_dst)

        # https://github.com/android-ndk/ndk/issues/372
        for root, dirs, files in os.walk(install_dir):
            if len(files) == 0 and len(dirs) == 0:
                with open(os.path.join(root, '.keep_dir'), 'w') as keep_file:
                    keep_file.write(
                        'This file forces git to keep the directory.')

        # TODO: This is overspecified.
        shutil.copy2(
            self.prebuilt_path('sysroot/NOTICE'),
            os.path.join(install_dir, 'NOTICE'))

        build_support.make_repo_prop(install_dir)
        self.validate_notice(install_dir)


class LibShaderc(ndk.builds.Module):
    name = 'libshaderc'
    path = 'sources/third_party/shaderc'

    def build(self, _build_dir, dist_dir, _args):
        shaderc_root_dir = build_support.android_path('external/shaderc')

        copies = [
            {
                'source_dir': os.path.join(shaderc_root_dir, 'shaderc'),
                'dest_dir': 'shaderc',
                'files': [
                    'Android.mk', 'libshaderc/Android.mk',
                    'libshaderc_util/Android.mk',
                    'third_party/Android.mk',
                    'utils/update_build_version.py',
                    'CHANGES',
                ],
                'dirs': [
                    'libshaderc/include', 'libshaderc/src',
                    'libshaderc_util/include', 'libshaderc_util/src',
                ],
            },
            {
                'source_dir': os.path.join(shaderc_root_dir, 'spirv-tools'),
                'dest_dir': 'shaderc/third_party/spirv-tools',
                'files': [
                    'utils/generate_grammar_tables.py',
                    'utils/generate_registry_tables.py',
                    'utils/update_build_version.py',
                    'CHANGES',
                ],
                'dirs': ['include', 'source'],
            },
            {
                'source_dir': os.path.join(shaderc_root_dir, 'spirv-headers'),
                'dest_dir':
                    'shaderc/third_party/spirv-tools/external/spirv-headers',
                'dirs': ['include'],
                'files': [
                    'include/spirv/1.0/spirv.py',
                    'include/spirv/1.1/spirv.py'
                ],
            },
            {
                'source_dir': os.path.join(shaderc_root_dir, 'glslang'),
                'dest_dir': 'shaderc/third_party/glslang',
                'files': ['glslang/OSDependent/osinclude.h'],
                'dirs': [
                    'SPIRV',
                    'OGLCompilersDLL',
                    'glslang/GenericCodeGen',
                    'hlsl',
                    'glslang/Include',
                    'glslang/MachineIndependent',
                    'glslang/OSDependent/Unix',
                    'glslang/Public',
                ],
            },
        ]

        default_ignore_patterns = shutil.ignore_patterns(
            "*CMakeLists.txt",
            "*.py",
            "*test.h",
            "*test.cc")

        temp_dir = tempfile.mkdtemp()
        shaderc_path = os.path.join(temp_dir, 'shaderc')
        try:
            for properties in copies:
                source_dir = properties['source_dir']
                dest_dir = os.path.join(temp_dir, properties['dest_dir'])
                for d in properties['dirs']:
                    src = os.path.join(source_dir, d)
                    dst = os.path.join(dest_dir, d)
                    print(src, " -> ", dst)
                    shutil.copytree(src, dst,
                                    ignore=default_ignore_patterns)
                for f in properties['files']:
                    print(source_dir, ':', dest_dir, ":", f)
                    # Only copy if the source file exists.  That way
                    # we can update this script in anticipation of
                    # source files yet-to-come.
                    if os.path.exists(os.path.join(source_dir, f)):
                        install_file(f, source_dir, dest_dir)
                    else:
                        print(source_dir, ':', dest_dir, ":", f, "SKIPPED")

            shaderc_shaderc_dir = os.path.join(shaderc_root_dir, 'shaderc')
            build_support.merge_license_files(
                os.path.join(shaderc_path, 'NOTICE'), [
                    os.path.join(shaderc_shaderc_dir, 'LICENSE'),
                    os.path.join(shaderc_shaderc_dir,
                                 'third_party',
                                 'LICENSE.spirv-tools'),
                    os.path.join(shaderc_shaderc_dir,
                                 'third_party',
                                 'LICENSE.glslang')])
            build_support.make_package('libshaderc', shaderc_path, dist_dir)
        finally:
            shutil.rmtree(temp_dir)


class CpuFeatures(ndk.builds.PackageModule):
    name = 'cpufeatures'
    path = 'sources/android/cpufeatures'
    src = build_support.ndk_path('sources/android/cpufeatures')
    create_repo_prop = True


class NativeAppGlue(ndk.builds.PackageModule):
    name = 'native_app_glue'
    path = 'sources/android/native_app_glue'
    src = build_support.ndk_path('sources/android/native_app_glue')
    create_repo_prop = True


class NdkHelper(ndk.builds.PackageModule):
    name = 'ndk_helper'
    path = 'sources/android/ndk_helper'
    src = build_support.ndk_path('sources/android/ndk_helper')
    create_repo_prop = True


class Gtest(ndk.builds.PackageModule):
    name = 'gtest'
    path = 'sources/third_party/googletest'
    src = build_support.ndk_path('sources/third_party/googletest')
    create_repo_prop = True


class Sysroot(ndk.builds.Module):
    name = 'sysroot'
    path = 'sysroot'

    def build(self, _out_dir, dist_dir, args):
        temp_dir = tempfile.mkdtemp()
        try:
            path = build_support.android_path('prebuilts/ndk/platform/sysroot')
            install_path = os.path.join(temp_dir, 'sysroot')
            shutil.copytree(path, install_path)
            if args.system != 'linux':
                # linux/netfilter has some headers with names that differ only
                # by case, which can't be extracted to a case-insensitive
                # filesystem, which are the defaults for Darwin and Windows :(
                #
                # There isn't really a good way to decide which of these to
                # keep and which to remove. The capitalized versions expose
                # different APIs, but we can't keep both. So far no one has
                # filed bugs about needing either API, so let's just dedup them
                # consistently and we can change that if we hear otherwise.
                remove_paths = [
                    'usr/include/linux/netfilter_ipv4/ipt_ECN.h',
                    'usr/include/linux/netfilter_ipv4/ipt_TTL.h',
                    'usr/include/linux/netfilter_ipv6/ip6t_HL.h',
                    'usr/include/linux/netfilter/xt_CONNMARK.h',
                    'usr/include/linux/netfilter/xt_DSCP.h',
                    'usr/include/linux/netfilter/xt_MARK.h',
                    'usr/include/linux/netfilter/xt_RATEEST.h',
                    'usr/include/linux/netfilter/xt_TCPMSS.h',
                ]
                for remove_path in remove_paths:
                    os.remove(os.path.join(install_path, remove_path))

            ndk_version_h_path = os.path.join(
                install_path, 'usr/include/android/ndk-version.h')
            with open(ndk_version_h_path, 'w') as ndk_version_h:
                major = config.major
                minor = config.hotfix
                beta = config.beta
                canary = '1' if config.canary else '0'
                build = args.build_number
                if build == 'dev':
                    build = '-1'

                ndk_version_h.write(textwrap.dedent("""\
                    #ifndef ANDROID_NDK_VERSION_H
                    #define ANDROID_NDK_VERSION_H

                    /**
                     * Major vision of this NDK.
                     *
                     * For example: 16 for r16.
                     */
                    #define __NDK_MAJOR__ {major}

                    /**
                     * Minor vision of this NDK.
                     *
                     * For example: 1 for r16b.
                     */
                    #define __NDK_MINOR__ {minor}

                    /**
                     * Beta vision of this NDK.
                     *
                     * For example: 1 for r16 beta 1, 0 for r16.
                     */
                    #define __NDK_BETA__ {beta}

                    /**
                     * Build number for this NDK.
                     *
                     * For a local development build of the NDK, this is -1.
                     */
                    #define __NDK_BUILD__ {build}

                    /**
                     * Set to 1 if this is a canary build, 0 if not.
                     */
                    #define __NDK_CANARY__ {canary}

                    #endif  /* ANDROID_NDK_VERSION_H */
                    """.format(
                        major=major,
                        minor=minor,
                        beta=beta,
                        build=build,
                        canary=canary)))

            build_support.make_package('sysroot', install_path, dist_dir)
        finally:
            shutil.rmtree(temp_dir)


class Vulkan(ndk.builds.Module):
    name = 'vulkan'
    path = 'sources/third_party/vulkan'

    def build(self, out_dir, dist_dir, args):
        print('Constructing Vulkan validation layer source...')
        vulkan_root_dir = build_support.android_path(
            'external/vulkan-validation-layers')

        copies = [
            {
                'source_dir': vulkan_root_dir,
                'dest_dir': 'vulkan/src',
                'files': [
                ],
                'dirs': [
                    'layers', 'include', 'tests', 'common', 'libs', 'scripts'
                ],
            },
            {
                'source_dir': vulkan_root_dir + '/loader',
                'dest_dir': 'vulkan/src/loader',
                'files': [
                    'vk_loader_platform.h',
                    'vk_loader_layer.h'
                ],
                'dirs': [],
            }
        ]

        default_ignore_patterns = shutil.ignore_patterns(
            "*CMakeLists.txt",
            "*test.cc",
            "linux",
            "windows")

        base_vulkan_path = os.path.join(out_dir, 'vulkan')
        vulkan_path = os.path.join(base_vulkan_path, 'src')
        for properties in copies:
            source_dir = properties['source_dir']
            dest_dir = os.path.join(out_dir, properties['dest_dir'])
            for d in properties['dirs']:
                src = os.path.join(source_dir, d)
                dst = os.path.join(dest_dir, d)
                shutil.rmtree(dst, True)
                shutil.copytree(src, dst,
                                ignore=default_ignore_patterns)
            for f in properties['files']:
                install_file(f, source_dir, dest_dir)

        # Copy Android build components
        print('Copying Vulkan build components...')
        src = os.path.join(vulkan_root_dir, 'build-android')
        dst = os.path.join(vulkan_path, 'build-android')
        shutil.rmtree(dst, True)
        shutil.copytree(src, dst, ignore=default_ignore_patterns)
        print('Copying finished')

        # Copy binary validation layer libraries
        print('Copying Vulkan binary validation layers...')
        src = build_support.android_path(
            'prebuilts/ndk/vulkan-validation-layers')
        dst = os.path.join(vulkan_path, 'build-android/jniLibs')
        shutil.rmtree(dst, True)
        shutil.copytree(src, dst, ignore=default_ignore_patterns)
        print('Copying finished')

        build_support.merge_license_files(
            os.path.join(base_vulkan_path, 'NOTICE'),
            [os.path.join(vulkan_root_dir, 'LICENSE.txt')])

        build_cmd = [
            'bash', vulkan_path + '/build-android/android-generate.sh'
        ]
        print('Generating generated layers...')
        subprocess.check_call(build_cmd)
        print('Generation finished')

        build_args = common_build_args(out_dir, dist_dir, args)
        if args.arch is not None:
            build_args.append('--arch={}'.format(args.arch))
        build_args.append('--no-symbols')

        # TODO: Verify source packaged properly
        print('Packaging Vulkan source...')
        src = os.path.join(out_dir, 'vulkan')
        build_support.make_package('vulkan', src, dist_dir)
        print('Packaging Vulkan source finished')


class NdkBuild(ndk.builds.PackageModule):
    name = 'ndk-build'
    path = 'build'
    src = build_support.ndk_path('build')
    create_repo_prop = True


# TODO(danalbert): Why isn't this just PackageModule?
class PythonPackages(ndk.builds.Module):
    name = 'python-packages'
    path = 'python-packages'

    def build(self, _build_dir, dist_dir, _args):
        # Stage the files in a temporary directory to make things easier.
        temp_dir = tempfile.mkdtemp()
        try:
            path = os.path.join(temp_dir, 'python-packages')
            shutil.copytree(
                build_support.android_path('development/python-packages'),
                path)
            build_support.make_package('python-packages', path, dist_dir)
        finally:
            shutil.rmtree(temp_dir)


class Gabixx(ndk.builds.PackageModule):
    name = 'gabi++'
    path = 'sources/cxx-stl/gabi++'
    src = build_support.ndk_path('sources/cxx-stl/gabi++')
    create_repo_prop = True


class SystemStl(ndk.builds.PackageModule):
    name = 'system-stl'
    path = 'sources/cxx-stl/system'
    src = build_support.ndk_path('sources/cxx-stl/system')
    create_repo_prop = True


class LibAndroidSupport(ndk.builds.PackageModule):
    name = 'libandroid_support'
    path = 'sources/android/support'
    src = build_support.ndk_path('sources/android/support')
    create_repo_prop = True


class Libcxxabi(ndk.builds.PackageModule):
    name = 'libc++abi'
    path = 'sources/cxx-stl/llvm-libc++abi'
    src = build_support.android_path('external/libcxxabi')
    create_repo_prop = True


class SimplePerf(ndk.builds.Module):
    name = 'simpleperf'
    path = 'simpleperf'

    def build(self, out_dir, dist_dir, args):
        print('Building simpleperf...')
        install_dir = os.path.join(out_dir, 'simpleperf')
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        os.makedirs(install_dir)

        simpleperf_path = build_support.android_path('prebuilts/simpleperf')
        dirs = ['doc', 'inferno', 'bin/android']
        is_win = args.system.startswith('windows')
        host_bin_dir = 'windows' if is_win else args.system
        dirs.append(os.path.join('bin/', host_bin_dir))
        for d in dirs:
            shutil.copytree(os.path.join(simpleperf_path, d),
                            os.path.join(install_dir, d))

        for item in os.listdir(simpleperf_path):
            should_copy = False
            if item.endswith('.py') and item not in ['update.py', 'test.py',
                                                     'report_html.py']:
                should_copy = True
            elif item == 'inferno.sh' and not is_win:
                should_copy = True
            elif item == 'inferno.bat' and is_win:
                should_copy = True
            if should_copy:
                shutil.copy2(os.path.join(simpleperf_path, item), install_dir)

        for f in ['NOTICE', 'ChangeLog']:
            shutil.copy2(os.path.join(simpleperf_path, f), install_dir)

        build_support.make_package('simpleperf', install_dir, dist_dir)


class RenderscriptLibs(ndk.builds.PackageModule):
    name = 'renderscript-libs'
    path = 'sources/android/renderscript'
    src = build_support.ndk_path('sources/android/renderscript')
    create_repo_prop = True


class RenderscriptToolchain(ndk.builds.InvokeBuildModule):
    name = 'renderscript-toolchain'
    path = 'toolchains/renderscript/prebuilt/{host}'
    script = 'build-renderscript.py'


class Changelog(ndk.builds.FileModule):
    name = 'changelog'
    path = 'CHANGELOG.md'
    src = build_support.ndk_path('CHANGELOG.md')

    def validate_notice(self, _install_base):
        # No license needed for the changelog.
        pass


class NdkGdbShortcut(ndk.builds.ScriptShortcutModule):
    name = 'ndk-gdb-shortcut'
    path = 'ndk-gdb'
    script = 'prebuilt/{host}/bin/ndk-gdb'
    windows_ext = '.cmd'


class NdkWhichShortcut(ndk.builds.ScriptShortcutModule):
    name = 'ndk-which-shortcut'
    path = 'ndk-which'
    script = 'prebuilt/{host}/bin/ndk-which'
    windows_ext = ''  # There isn't really a Windows ndk-which.


class NdkDependsShortcut(ndk.builds.ScriptShortcutModule):
    name = 'ndk-depends-shortcut'
    path = 'ndk-depends'
    script = 'prebuilt/{host}/bin/ndk-depends'
    windows_ext = '.exe'


class NdkStackShortcut(ndk.builds.ScriptShortcutModule):
    name = 'ndk-stack-shortcut'
    path = 'ndk-stack'
    script = 'prebuilt/{host}/bin/ndk-stack'
    windows_ext = '.exe'


class NdkBuildShortcut(ndk.builds.ScriptShortcutModule):
    name = 'ndk-build-shortcut'
    path = 'ndk-build'
    script = 'build/ndk-build'
    windows_ext = '.cmd'


class Readme(ndk.builds.FileModule):
    name = 'readme'
    path = 'README.md'
    src = build_support.ndk_path('UserReadme.md')


CANARY_TEXT = textwrap.dedent("""\
    This is a canary build of the Android NDK. It's updated almost every day.

    Canary builds are designed for early adopters and can be prone to breakage.
    Sometimes they can break completely. To aid development and testing, this
    distribution can be installed side-by-side with your existing, stable NDK
    release.
    """)


class CanaryReadme(ndk.builds.Module):
    name = 'canary-readme'
    path = 'README.canary'

    def build(self, _out_dir, _dist_dir, _args):
        pass

    def install(self, out_dir, _dist_dir, _args):
        if config.canary:
            extract_dir = ndk.paths.get_install_path(out_dir)
            canary_path = os.path.join(extract_dir, self.path)
            with open(canary_path, 'w') as canary_file:
                canary_file.write(CANARY_TEXT)


class Meta(ndk.builds.PackageModule):
    name = 'meta'
    path = 'meta'
    src = build_support.ndk_path('meta')

    def validate_notice(self, _install_base):
        # No license needed for meta.
        pass


class SourceProperties(ndk.builds.Module):
    name = 'source.properties'
    path = 'source.properties'

    def build(self, _out_dir, _dist_dir, _args):
        pass

    def install(self, out_dir, _dist_dir, args):
        install_dir = ndk.paths.get_install_path(out_dir)
        path = os.path.join(install_dir, self.path)
        with open(path, 'w') as source_properties:
            version = '{}.{}.{}'.format(
                config.major, config.hotfix, args.build_number)
            if config.beta > 0:
                version += '-beta{}'.format(config.beta)
            source_properties.writelines([
                'Pkg.Desc = Android NDK\n',
                'Pkg.Revision = {}\n'.format(version)
            ])


def launch_build(worker, module, out_dir, dist_dir, args, log_dir):
    log_path = os.path.join(log_dir, module.log_file)
    with open(log_path, 'w') as log_file:
        os.dup2(log_file.fileno(), sys.stdout.fileno())
        os.dup2(log_file.fileno(), sys.stderr.fileno())
        try:
            worker.status = 'Building {}...'.format(module)
            module.build(out_dir, dist_dir, args)
            return module, True, log_path
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()
            return module, False, log_path


def do_install(worker, module, out_dir, dist_dir, args):
    worker.status = 'Installing {}...'.format(module)
    module.install(out_dir, dist_dir, args)


def split_module_by_arch(module, arches):
    if module.split_build_by_arch:
        for arch in arches:
            build_module = copy.deepcopy(module)
            build_module.build_arch = arch
            yield build_module
    else:
        yield module


def get_modules_to_build(module_names, arches):
    modules = []
    for module in ALL_MODULES:
        if module.name in module_names:
            for build_module in split_module_by_arch(module, arches):
                modules.append(build_module)
    return modules


ALL_MODULES = [
    CanaryReadme(),
    Changelog(),
    Clang(),
    CpuFeatures(),
    Gabixx(),
    Gcc(),
    GdbServer(),
    Gnustl(),
    Gtest(),
    HostTools(),
    LibAndroidSupport(),
    LibShaderc(),
    Libcxx(),
    Libcxxabi(),
    Meta(),
    NativeAppGlue(),
    NdkBuild(),
    NdkBuildShortcut(),
    NdkDepends(),
    NdkDependsShortcut(),
    NdkGdbShortcut(),
    NdkHelper(),
    NdkStack(),
    NdkStackShortcut(),
    NdkWhichShortcut(),
    Platforms(),
    PythonPackages(),
    Readme(),
    RenderscriptLibs(),
    RenderscriptToolchain(),
    ShaderTools(),
    SimplePerf(),
    SourceProperties(),
    Stlport(),
    Sysroot(),
    SystemStl(),
    Vulkan(),
]


def get_all_module_names():
    return [m.name for m in ALL_MODULES]


def parse_args():
    parser = argparse.ArgumentParser(
        description=inspect.getdoc(sys.modules[__name__]))

    parser.add_argument(
        '--arch',
        choices=('arm', 'arm64', 'x86', 'x86_64'),
        help='Build for the given architecture. Build all by default.')
    parser.add_argument(
        '-j', '--jobs', type=int, default=multiprocessing.cpu_count(),
        help=('Number of parallel builds to run. Note that this will not '
              'affect the -j used for make; this just parallelizes '
              'checkbuild.py. Defaults to the number of CPUs available.'))

    package_group = parser.add_mutually_exclusive_group()
    package_group.add_argument(
        '--package', action='store_true', dest='package', default=True,
        help='Package the NDK when done building (default).')
    package_group.add_argument(
        '--no-package', action='store_false', dest='package',
        help='Do not package the NDK when done building.')
    package_group.add_argument(
        '--force-package', action='store_true', dest='force_package',
        help='Force a package even if only building a subset of modules.')

    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        '--build-tests', action='store_true', dest='build_tests', default=True,
        help=textwrap.dedent("""\
        Build tests when finished. --package is required. Not supported
        when targeting Windows.
        """))
    test_group.add_argument(
        '--no-build-tests', action='store_false', dest='build_tests',
        help='Skip building tests after building the NDK.')

    parser.add_argument(
        '--build-number', default='dev',
        help='Build number for use in version files.')
    parser.add_argument(
        '--release', help='Ignored. Temporarily compatibility.')

    parser.add_argument(
        '--system', choices=('darwin', 'linux', 'windows', 'windows64'),
        default=build_support.get_default_host(),
        help='Build for the given OS.')

    module_group = parser.add_mutually_exclusive_group()

    module_group.add_argument(
        '--module', dest='modules', action='append',
        choices=get_all_module_names(), help='NDK modules to build.')

    module_group.add_argument(
        '--host-only', action='store_true',
        help='Skip building target components.')

    return parser.parse_args()


def log_build_failure(log_path, dist_dir):
    with open(log_path, 'r') as log_file:
        contents = log_file.read()
        print(contents)

        # The build server has a build_error.log file that is supposed to be
        # the short log of the failure that stopped the build. Append our
        # failing log to that.
        build_error_log = os.path.join(dist_dir, 'logs/build_error.log')
        with open(build_error_log, 'a') as error_log:
            error_log.write('\n')
            error_log.write(contents)


def wait_for_build(workqueue, dist_dir):
    console = ndk.ansi.get_console()
    ui = ndk.ui.get_build_progress_ui(console, workqueue)
    with ndk.ansi.disable_terminal_echo(sys.stdin):
        with console.cursor_hide_context():
            while not workqueue.finished():
                module, result, log_path = workqueue.get_result()
                if not result:
                    ui.clear()
                    print('Build failed: {}'.format(module))
                    log_build_failure(log_path, dist_dir)
                    sys.exit(1)
                elif not console.smart_console:
                    ui.clear()
                    print('Build succeeded: {}'.format(module))
                ui.draw()
            ui.clear()
            print('Build finished')


def wait_for_install(workqueue):
    console = ndk.ansi.get_console()
    ui = ndk.ui.get_build_progress_ui(console, workqueue)
    with ndk.ansi.disable_terminal_echo(sys.stdin):
        with console.cursor_hide_context():
            while not workqueue.finished():
                workqueue.get_result()
                ui.draw()
            ui.clear()
            print('Install finished')


def main():
    logging.basicConfig()

    total_timer = ndk.timer.Timer()
    total_timer.start()

    # It seems the build servers run us in our own session, in which case we
    # get EPERM from `setpgrp`. No need to call this in that case because we
    # will already be the process group leader.
    if os.getpid() != os.getsid(os.getpid()):
        os.setpgrp()

    args = parse_args()

    if args.modules is None:
        module_names = get_all_module_names()
    else:
        module_names = args.modules

    if args.host_only:
        module_names = [
            'clang',
            'gcc',
            'host-tools',
            'ndk-build',
            'python-packages',
            'renderscript-toolchain',
            'shader-tools',
            'simpleperf',
        ]

    required_package_modules = set(get_all_module_names())
    have_required_modules = required_package_modules <= set(module_names)
    if (args.package and have_required_modules) or args.force_package:
        do_package = True
    else:
        do_package = False

    # TODO(danalbert): wine?
    # We're building the Windows packages from Linux, so we can't actually run
    # any of the tests from here.
    if args.system.startswith('windows') or not do_package:
        args.build_tests = False

    # Disable buffering on stdout so the build output doesn't hide all of our
    # "Building..." messages.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # Set ANDROID_BUILD_TOP.
    if 'ANDROID_BUILD_TOP' in os.environ:
        sys.exit(textwrap.dedent("""\
            Error: ANDROID_BUILD_TOP is already set in your environment.

            This typically means you are running in a shell that has lunched a
            target in a platform build. The platform environment interferes
            with the NDK build environment, so the build cannot continue.

            Launch a new shell before building the NDK."""))

    os.environ['ANDROID_BUILD_TOP'] = os.path.realpath('..')

    out_dir = build_support.get_out_dir()
    dist_dir = build_support.get_dist_dir(out_dir)

    print('Cleaning up...')
    invoke_build('dev-cleanup.sh')

    print('Building modules: {}'.format(' '.join(module_names)))
    print('Machine has {} CPUs'.format(multiprocessing.cpu_count()))

    arches = build_support.ALL_ARCHITECTURES
    if args.arch is not None:
        arches = [args.arch]
    modules = get_modules_to_build(module_names, arches)

    log_dir = os.path.join(dist_dir, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    build_timer = ndk.timer.Timer()
    workqueue = ndk.workqueue.WorkQueue(args.jobs)
    try:
        with build_timer:
            for module in modules:
                workqueue.add_task(
                    launch_build, module, out_dir, dist_dir, args, log_dir)

            wait_for_build(workqueue, dist_dir)

        ndk_dir = ndk.paths.get_install_path(out_dir)
        install_timer = ndk.timer.Timer()
        with install_timer:
            if not os.path.exists(ndk_dir):
                os.makedirs(ndk_dir)
            for module in modules:
                workqueue.add_task(
                    do_install, module, out_dir, dist_dir, args)

            wait_for_install(workqueue)
    finally:
        workqueue.terminate()
        workqueue.join()

    package_timer = ndk.timer.Timer()
    with package_timer:
        if do_package:
            print('Packaging NDK...')
            host_tag = build_support.host_to_tag(args.system)
            package_ndk(ndk_dir, dist_dir, host_tag, args.build_number)

    good = True
    test_timer = ndk.timer.Timer()
    with test_timer:
        if args.build_tests:
            good = build_ndk_tests(out_dir, dist_dir, args)
            print()  # Blank line between test results and timing data.

    total_timer.finish()

    print('Finished {}'.format('successfully' if good else 'unsuccessfully'))
    print('Build: {}'.format(build_timer.duration))
    print('Install: {}'.format(install_timer.duration))
    print('Packaging: {}'.format(package_timer.duration))
    print('Testing: {}'.format(test_timer.duration))
    print('Total: {}'.format(total_timer.duration))

    subject = 'NDK Build {}!'.format('Passed' if good else 'Failed')
    body = 'Build finished in {}'.format(total_timer.duration)
    ndk.notify.toast(subject, body)

    sys.exit(not good)


if __name__ == '__main__':
    main()
