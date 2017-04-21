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
"""APIs for enumerating and building NDK tests."""
from __future__ import absolute_import

import itertools
import logging
import os
import shutil
import yaml

import build.lib.build_support
import ndk.abis
import ndk.os
import ndk.test.spec

import tests.filters as filters
import tests.testlib as testlib


def logger():
    """Returns the module logger."""
    return logging.getLogger(__name__)


def test_spec_from_config(test_config):
    """Returns a TestSpec based on the test config file."""
    abis = test_config.get('abis', build.lib.build_support.ALL_ABIS)
    toolchains = test_config.get('toolchains', ['clang', '4.9'])
    headers_configs = test_config.get('headers', ['unified', 'deprecated'])
    pie_configs = test_config.get('pie', [True, False])
    suites = test_config.get('suites', testlib.ALL_SUITES)

    # Duplicate this so we don't modify the list in test_config.
    headers_configs = list(headers_configs)
    for i, headers_config in enumerate(headers_configs):
        if headers_config == 'unified':
            headers_configs[i] = False
        elif headers_config == 'deprecated':
            headers_configs[i] = True
        else:
            raise ValueError('Invalid headers config: ' + headers_config)

    return ndk.test.spec.TestSpec(
        abis, toolchains, headers_configs, pie_configs, suites)


def build_test_runner(test_spec, test_options, printer):
    runner = testlib.TestRunner(printer)

    build_configs = itertools.product(
        test_spec.abis,
        test_spec.toolchains,
        test_spec.headers_config,
        test_spec.pie_config)

    scanner = testlib.BuildTestScanner()
    nodist_scanner = testlib.BuildTestScanner(dist=False)
    libcxx_scanner = testlib.LibcxxTestScanner(test_options.ndk_path)
    for abi, toolchain, headers_config, pie_config in build_configs:
        if pie_config and abi in ndk.abis.LP64_ABIS:
            # We don't need to build both PIE configurations for LP64 ABIs
            # since all of them support PIE. Just build the default
            # configuration.
            continue

        scanner.add_build_configuration(
            abi,
            None,  # Build API level, always default.
            toolchain,
            pie_config,
            test_options.verbose_build,
            headers_config)

        nodist_scanner.add_build_configuration(
            abi,
            None,  # Build API level, always default.
            toolchain,
            pie_config,
            test_options.verbose_build,
            headers_config)

        libcxx_scanner.add_build_configuration(
            abi,
            None,  # Build API level, always default.
            toolchain,
            pie_config,
            test_options.verbose_build,
            headers_config)

    if 'build' in test_spec.suites:
        runner.add_suite('build', 'tests/build', nodist_scanner)
    if 'device' in test_spec.suites:
        runner.add_suite('device', 'tests/device', scanner)
    if 'libc++' in test_spec.suites:
        runner.add_suite('libc++', 'tests/libc++', libcxx_scanner)

    return runner


class TestBuilder(object):
    def __init__(self, test_spec, test_options, printer):
        self.runner = build_test_runner(test_spec, test_options, printer)

        self.test_options = test_options

        self.obj_dir = os.path.join(self.test_options.out_dir, 'obj')
        self.dist_dir = os.path.join(self.test_options.out_dir, 'dist')

    @classmethod
    def from_config_file(cls, config_path, test_options, printer):
        with open(config_path) as test_config_file:
            test_config = yaml.load(test_config_file)
        spec = test_spec_from_config(test_config)
        return cls(spec, test_options, printer)

    def make_out_dirs(self):
        if not os.path.exists(self.obj_dir):
            os.makedirs(self.obj_dir)
        if not os.path.exists(self.dist_dir):
            os.makedirs(self.dist_dir)

    def clean_out_dir(self):
        if os.path.exists(self.test_options.out_dir):
            shutil.rmtree(self.test_options.out_dir)

    def build(self):
        if self.test_options.clean:
            self.clean_out_dir()
        self.make_out_dirs()

        test_filters = filters.TestFilter.from_string(
            self.test_options.test_filter)
        with ndk.os.modify_environ({'NDK': self.test_options.ndk_path}):
            return self.runner.run(self.obj_dir, self.dist_dir, test_filters)
