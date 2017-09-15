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
"""Defines the NDK build system API.

Note: this isn't the ndk-build API, but the API for building the NDK itself.
"""
from __future__ import absolute_import

import ntpath
import os
import shutil
import stat
import subprocess

import build.lib.build_support
import ndk.packaging
import ndk.paths


class ModuleValidateError(RuntimeError):
    pass


class Module(object):
    name = None
    path = None

    # If split_build_by_arch is set, one workqueue task will be created for
    # each architecture. The Module object will be cloned for each arch and
    # each will have build_arch set to the architecture that should be built by
    # that module. If build_arch is None, the module has not yet been split.
    split_build_by_arch = False
    build_arch = None

    def __init__(self):
        self.validate()

    def validate_error(self, msg):
        return ModuleValidateError('{}: {}'.format(self.name, msg))

    def validate(self):
        if self.name is None:
            raise ModuleValidateError('{} has no name'.format(self.__class__))
        if self.path is None:
            raise self.validate_error('path property not set')

    def build(self, build_dir, dist_dir, args):
        raise NotImplementedError

    def install(self, out_dir, dist_dir, args):
        arches = build.lib.build_support.ALL_ARCHITECTURES
        if args.arch is not None:
            arches = [args.arch]
        package_installs = ndk.packaging.expand_packages(
            self.name, self.path, args.system, arches)

        install_base = ndk.paths.get_install_path(out_dir)
        for package_name, package_install in package_installs:
            install_path = os.path.join(install_base, package_install)
            package = os.path.join(dist_dir, package_name)
            if os.path.exists(install_path):
                shutil.rmtree(install_path)
            ndk.packaging.extract_zip(package, install_path)

            self.validate_notice(install_path)

    def get_install_paths(self, build_dir, host, arches):
        install_subdirs = ndk.packaging.expand_paths(self.path, host, arches)
        install_base = ndk.paths.get_install_path(build_dir)
        return [os.path.join(install_base, d) for d in install_subdirs]

    def get_install_path(self, build_dir, host, arch=None):
        arch_dependent = False
        if ndk.packaging.package_varies_by(self.path, 'abi'):
            arch_dependent = True
        elif ndk.packaging.package_varies_by(self.path, 'arch'):
            arch_dependent = True
        elif ndk.packaging.package_varies_by(self.path, 'toolchain'):
            arch_dependent = True
        elif ndk.packaging.package_varies_by(self.path, 'triple'):
            arch_dependent = True

        arches = None
        if arch is not None:
            arches = [arch]
        elif arch_dependent:
            raise ValueError(
                'get_install_path for {} requires valid arch'.format(arch))

        install_subdirs = self.get_install_paths(build_dir, host, arches)

        if len(install_subdirs) != 1:
            raise RuntimeError(
                'non-unique install path for single arch: ' + self.path)

        return install_subdirs[0]

    def validate_notice(self, install_path):
        license_file = os.path.join(install_path, 'NOTICE')
        if not os.path.exists(license_file):
            raise RuntimeError('{} did not install a NOTICE file at {}'.format(
                self.name, license_file))

        repo_prop_file = os.path.join(install_path, 'repo.prop')
        if not os.path.exists(repo_prop_file):
            raise RuntimeError(
                '{} did not install a repo.prop file at {}'.format(
                    self.name, repo_prop_file))

    def __str__(self):
        if self.split_build_by_arch and self.build_arch is not None:
            return '{} [{}]'.format(self.name, self.build_arch)
        return self.name

    @property
    def log_file(self):
        if self.split_build_by_arch and self.build_arch is not None:
            return '{}-{}.log'.format(self.name, self.build_arch)
        elif self.split_build_by_arch:
            raise RuntimeError('Called log_file on unsplit module')
        else:
            return '{}.log'.format(self.name)


class PackageModule(Module):
    src = None
    create_repo_prop = False

    def validate(self):
        super(PackageModule, self).validate()

        if ndk.packaging.package_varies_by(self.path, 'abi'):
            raise self.validate_error(
                'PackageModule cannot vary by abi')
        if ndk.packaging.package_varies_by(self.path, 'arch'):
            raise self.validate_error(
                'PackageModule cannot vary by arch')
        if ndk.packaging.package_varies_by(self.path, 'toolchain'):
            raise self.validate_error(
                'PackageModule cannot vary by toolchain')
        if ndk.packaging.package_varies_by(self.path, 'triple'):
            raise self.validate_error(
                'PackageModule cannot vary by triple')

    def build(self, _build_dir, _dist_dir, _args):
        pass

    def install(self, build_dir, _dist_dir, args):
        install_paths = self.get_install_paths(
            build_dir, args.system, build.lib.build_support.ALL_ARCHITECTURES)
        assert len(install_paths) == 1
        install_path = install_paths[0]
        install_directory(self.src, install_path)
        if self.create_repo_prop:
            build.lib.build_support.make_repo_prop(install_path)
        self.validate_notice(install_path)


class InvokeExternalBuildModule(Module):
    script = None
    arch_specific = False

    def build(self, build_dir, dist_dir, args):
        build_args = common_build_args(build_dir, dist_dir, args)
        if self.split_build_by_arch:
            build_args.append('--arch={}'.format(self.build_arch))
        elif self.arch_specific and args.arch is not None:
            build_args.append('--arch={}'.format(args.arch))
        build_args.extend(self.additional_args(args))
        script = self.get_script_path()
        invoke_external_build(script, build_args)

    def get_script_path(self):
        return build.lib.build_support.android_path(self.script)

    def additional_args(self, _args):  # pylint: disable=no-self-use
        return []


class InvokeBuildModule(InvokeExternalBuildModule):
    def get_script_path(self):
        return build.lib.build_support.ndk_path('build/tools', self.script)


class FileModule(Module):
    src = None

    def build(self, _build_dir, _dist_dir, _args):
        pass

    def install(self, out_dir, dist_dir, args):
        install_base = ndk.paths.get_install_path(out_dir)
        install_path = os.path.join(install_base, self.path)
        if os.path.exists(install_path):
            os.remove(install_path)
        shutil.copy2(self.src, install_path)


class ScriptShortcutModule(Module):
    script = None
    windows_ext = None

    def validate_notice(self, _install_base):
        # These are all trivial shell scripts that we generated. No notice
        # needed.
        pass

    def validate(self):
        super(ScriptShortcutModule, self).validate()

        if ndk.packaging.package_varies_by(self.script, 'abi'):
            raise self.validate_error(
                'ScriptShortcutModule cannot vary by abi')
        if ndk.packaging.package_varies_by(self.script, 'arch'):
            raise self.validate_error(
                'ScriptShortcutModule cannot vary by arch')
        if ndk.packaging.package_varies_by(self.script, 'toolchain'):
            raise self.validate_error(
                'ScriptShortcutModule cannot vary by toolchain')
        if ndk.packaging.package_varies_by(self.script, 'triple'):
            raise self.validate_error(
                'ScriptShortcutModule cannot vary by triple')
        if self.windows_ext is None:
            raise self.validate_error(
                'ScriptShortcutModule requires windows_ext')

    def build(self, _build_dir, _dist_dir, _args):
        pass

    def install(self, out_dir, dist_dir, args):
        if args.system.startswith('windows'):
            self.make_cmd_helper(out_dir, args.system)
        else:
            self.make_sh_helper(out_dir, args.system)

    def make_cmd_helper(self, out_dir, system):
        script = self.get_script_path(system)
        full_path = ntpath.join(
            '%~dp0', ntpath.normpath(script) + self.windows_ext)

        install_base = ndk.paths.get_install_path(out_dir)
        install_path = os.path.join(install_base, self.path) + '.cmd'
        with open(os.path.join(install_path), 'w') as helper:
            helper.writelines([
                '@echo off\n',
                full_path + ' %*\n',
            ])

    def make_sh_helper(self, out_dir, system):
        script = self.get_script_path(system)

        install_base = ndk.paths.get_install_path(out_dir)
        install_path = os.path.join(install_base, self.path)

        full_path = os.path.join('$DIR', script)
        with open(install_path, 'w') as helper:
            helper.writelines([
                '#!/bin/sh\n',
                'DIR="$(cd "$(dirname "$0")" && pwd)"\n',
                full_path + ' "$@"',
            ])
        mode = os.stat(install_path).st_mode
        os.chmod(install_path,
                 mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def get_script_path(self, system):
        scripts = ndk.packaging.expand_paths(
            self.script, system, build.lib.build_support.ALL_ARCHITECTURES)
        assert len(scripts) == 1
        return scripts[0]


def _invoke_build(script, args):
    if args is None:
        args = []
    subprocess.check_call(
        [build.lib.build_support.android_path(script)] + args)


def invoke_build(script, args=None):
    script_path = os.path.join('build/tools', script)
    _invoke_build(
        build.lib.build_support.ndk_path(script_path), args)


def invoke_external_build(script, args=None):
    _invoke_build(
        build.lib.build_support.android_path(script), args)


def common_build_args(out_dir, dist_dir, args):
    return [
        '--out-dir={}'.format(out_dir),
        '--dist-dir={}'.format(dist_dir),
        '--host={}'.format(args.system),
    ]


def install_directory(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    ignore_patterns = shutil.ignore_patterns(
        '*.pyc', '*.pyo', '*.swp', '*.git*')
    shutil.copytree(src, dst, ignore=ignore_patterns)
