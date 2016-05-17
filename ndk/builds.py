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
import os
import subprocess

import build.lib.build_support


class Module(object):
    name = None

    def build(self, build_dir, dist_dir, args):
        raise NotImplementedError


class PackageModule(Module):
    src = None

    def build(self, build_dir, dist_dir, args):
        build.lib.build_support.make_package(self.name, self.src, dist_dir)


class InvokeExternalBuildModule(Module):
    script = None
    arch_specific = False

    def build(self, build_dir, dist_dir, args):
        build_args = common_build_args(build_dir, dist_dir, args)
        if self.arch_specific and args.arch is not None:
            build_args.append('--arch={}'.format(args.arch))
        script = self.get_script_path()
        invoke_external_build(script, build_args)

    def get_script_path(self):
        return build.lib.build_support.android_path(self.script)


class InvokeBuildModule(InvokeExternalBuildModule):
    def get_script_path(self):
        return build.lib.build_support.ndk_path('build/tools', self.script)


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
    build_args = ['--out-dir={}'.format(out_dir)]
    build_args = ['--dist-dir={}'.format(dist_dir)]
    build_args.append('--host={}'.format(args.system))
    return build_args
