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
"""Tests for ndk.test.report."""
import unittest

import ndk.test.report
import tests.testlib


class MockTest(object):
    is_flaky = True


class ReportTest(unittest.TestCase):
    def test_remove_all_failing_flaky(self):
        report = ndk.test.report.Report()
        report.add_result('build', tests.testlib.Success(MockTest()))
        report.add_result('build', tests.testlib.Failure(MockTest(), 'failed'))
        report.add_result('build', tests.testlib.Failure(
            MockTest(), 'Did not receive exit status from test.'))
        report.add_result('build', tests.testlib.Failure(
            MockTest(), 'text busy'))
        report.add_result('build', tests.testlib.Failure(
            MockTest(), 'Text file busy'))
        report.add_result('build', tests.testlib.Skipped(
            MockTest(), 'skipped'))
        report.add_result('build', tests.testlib.ExpectedFailure(
            MockTest(), 'bug', 'config'))
        report.add_result('build', tests.testlib.UnexpectedSuccess(
            MockTest(), 'bug', 'config'))

        results = report.remove_all_failing_flaky(tests.testlib.flake_filter)
        self.assertEqual(3, len(results))
