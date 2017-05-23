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
"""Test result classes."""
import tests.util


class TestResult(object):
    def __init__(self, test):
        self.test = test

    def __repr__(self):
        return self.to_string(colored=False)

    def passed(self):
        raise NotImplementedError

    def failed(self):
        raise NotImplementedError

    def to_string(self, colored=False):
        raise NotImplementedError


class Failure(TestResult):
    def __init__(self, test, message):
        super(Failure, self).__init__(test)
        self.message = message

    def passed(self):
        return False

    def failed(self):
        return True

    def to_string(self, colored=False):
        label = tests.util.maybe_color('FAIL', 'red', colored)
        return '{} {} [{}]: {}'.format(
            label, self.test.name, self.test.config, self.message)


class Success(TestResult):
    def passed(self):
        return True

    def failed(self):
        return False

    def to_string(self, colored=False):
        label = tests.util.maybe_color('PASS', 'green', colored)
        return '{} {} [{}]'.format(label, self.test.name, self.test.config)


class Skipped(TestResult):
    def __init__(self, test, reason):
        super(Skipped, self).__init__(test)
        self.reason = reason

    def passed(self):
        return False

    def failed(self):
        return False

    def to_string(self, colored=False):
        label = tests.util.maybe_color('SKIP', 'yellow', colored)
        return '{} {} [{}]: {}'.format(
            label, self.test.name, self.test.config, self.reason)


class ExpectedFailure(TestResult):
    def __init__(self, test, broken_config, bug):
        super(ExpectedFailure, self).__init__(test)
        self.broken_config = broken_config
        self.bug = bug

    def passed(self):
        return True

    def failed(self):
        return False

    def to_string(self, colored=False):
        label = tests.util.maybe_color('KNOWN FAIL', 'yellow', colored)
        return '{} {} [{}]: known failure for {} ({})'.format(
            label, self.test.name, self.test.config, self.broken_config,
            self.bug)


class UnexpectedSuccess(TestResult):
    def __init__(self, test, broken_config, bug):
        super(UnexpectedSuccess, self).__init__(test)
        self.broken_config = broken_config
        self.bug = bug

    def passed(self):
        return False

    def failed(self):
        return True

    def to_string(self, colored=False):
        label = tests.util.maybe_color('SHOULD FAIL', 'red', colored)
        return '{} {} [{}]: unexpected success for {} ({})'.format(
            label, self.test.name, self.test.config, self.broken_config,
            self.bug)
