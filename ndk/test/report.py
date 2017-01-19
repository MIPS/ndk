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
"""Defines the format of test results from the test runner."""


class SingleResultReport(object):
    """Stores the result of a single test with its config info."""
    def __init__(self, suite, result):
        self.suite = suite
        self.result = result


class Report(object):
    """Stores details of a test run.

    A "test run" means any number of tests run in any number of (unique)
    configurations.
    """
    def __init__(self):
        self.reports = []

    def add_result(self, suite, result):
        self.reports.append(SingleResultReport(suite, result))

    def by_suite(self):
        suite_reports = {}
        for report in self.reports:
            if report.suite not in suite_reports:
                suite_reports[report.suite] = Report()
            suite_reports[report.suite].add_result(report.suite, report.result)
        return suite_reports

    @property
    def successful(self):
        return self.num_failed == 0

    @property
    def num_tests(self):
        return len(self.reports)

    @property
    def num_failed(self):
        return len(self.all_failed)

    @property
    def num_passed(self):
        return len(self.all_passed)

    @property
    def num_skipped(self):
        return len(self.all_skipped)

    @property
    def all_failed(self):
        failures = []
        for report in self.reports:
            if report.result.failed():
                failures.append(report)
        return failures

    @property
    def all_passed(self):
        passes = []
        for report in self.reports:
            if report.result.passed():
                passes.append(report)
        return passes

    @property
    def all_skipped(self):
        skips = []
        for report in self.reports:
            if not report.result.passed() and not report.result.failed():
                skips.append(report)
        return skips
