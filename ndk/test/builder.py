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
import json
import logging
import multiprocessing
import os
import shutil

import build.lib.build_support
import ndk.abis
import ndk.test.spec
import ndk.workqueue

import tests.filters as filters
import tests.testlib as testlib


def logger():
    """Returns the module logger."""
    return logging.getLogger(__name__)


def test_spec_from_config(test_config):
    """Returns a TestSpec based on the test config file."""
    abis = test_config.get('abis', build.lib.build_support.ALL_ABIS)
    toolchains = test_config.get('toolchains', ['clang', '4.9'])
    pie_configs = test_config.get('pie', [True, False])
    suites = test_config.get('suites', testlib.ALL_SUITES)

    return ndk.test.spec.TestSpec(abis, toolchains, pie_configs, suites)


def build_test_runner(test_spec, test_options, printer):
    runner = testlib.TestRunner(printer)

    build_configs = itertools.product(
        test_spec.abis,
        test_spec.toolchains,
        test_spec.pie_config)

    scanner = testlib.BuildTestScanner(test_options.ndk_path)
    nodist_scanner = testlib.BuildTestScanner(
        test_options.ndk_path, dist=False)
    libcxx_scanner = testlib.LibcxxTestScanner(test_options.ndk_path)
    for abi, toolchain, pie_config in build_configs:
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
            test_options.verbose_build)

        nodist_scanner.add_build_configuration(
            abi,
            None,  # Build API level, always default.
            toolchain,
            pie_config,
            test_options.verbose_build)

        libcxx_scanner.add_build_configuration(
            abi,
            None,  # Build API level, always default.
            toolchain,
            pie_config,
            test_options.verbose_build)

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
            test_config = json.load(test_config_file)
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
        return self.runner.run(self.obj_dir, self.dist_dir, test_filters)


class LoadRestrictingWorkQueue(object):
    """Specialized work queue for building tests.

    Building the libc++ tests is very demanding and we should not be running
    more than one libc++ build at a time. The LoadRestrictingWorkQueue has a
    normal task queue as well as a task queue served by only one worker.
    """

    def __init__(self, num_workers=multiprocessing.cpu_count()):
        self.manager = multiprocessing.Manager()
        self.result_queue = self.manager.Queue()

        assert num_workers >= 2

        self.main_task_queue = self.manager.Queue()
        self.restricted_task_queue = self.manager.Queue()

        self.main_work_queue = ndk.workqueue.WorkQueue(
            num_workers - 1, task_queue=self.main_task_queue,
            result_queue=self.result_queue)

        self.restricted_work_queue = ndk.workqueue.WorkQueue(
            1, task_queue=self.restricted_task_queue,
            result_queue=self.result_queue)

        self.num_tasks = 0

    def add_task(self, func, *args, **kwargs):
        self.main_task_queue.put(ndk.workqueue.Task(func, args, kwargs))
        self.num_tasks += 1

    def add_load_restricted_task(self, func, *args, **kwargs):
        self.restricted_task_queue.put(ndk.workqueue.Task(func, args, kwargs))
        self.num_tasks += 1

    def get_result(self):
        """Gets a result from the queue, blocking until one is available."""
        result = self.result_queue.get()
        if isinstance(result, ndk.workqueue.TaskError):
            raise result
        self.num_tasks -= 1
        return result

    def terminate(self):
        self.main_work_queue.terminate()
        self.restricted_work_queue.terminate()

    def join(self):
        self.main_work_queue.join()
        self.restricted_work_queue.join()

    def finished(self):
        """Returns True if all tasks have completed execution."""
        return self.num_tasks == 0
