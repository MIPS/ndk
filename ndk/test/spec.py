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
"""Configuration objects for describing test runs."""


class TestOptions(object):
    """Configuration for how tests should be run."""
    def __init__(self, src_dir, ndk_path, out_dir, test_filter=None,
                 clean=True, build_report=None):
        """Initializes a TestOptions object.

        Args:
            src_dir: Path to the tests.
            ndk_path: Path to the NDK to use to build the tests.
            out_dir: Test output directory.
            test_filter: Test filter string.
            clean: True if the out directory should be cleaned before building.
            build_report: Path to write a build report to, if any.
        """
        self.src_dir = src_dir
        self.ndk_path = ndk_path
        self.out_dir = out_dir
        self.test_filter = test_filter
        self.clean = clean
        self.build_report = build_report


class TestSpec(object):
    """Configuration for which tests should be run."""
    def __init__(self, abis, toolchains, pie_config, suites):
        self.abis = abis
        self.toolchains = toolchains
        self.pie_config = pie_config
        self.suites = suites


class BuildConfiguration(object):
    """A configuration for a single test build.

    A TestSpec describes which BuildConfigurations should be included in a test
    run.
    """
    def __init__(self, abi, api, toolchain, force_pie):
        self.abi = abi
        self.api = api
        self.toolchain = toolchain
        self.force_pie = force_pie

    def __eq__(self, other):
        if self.abi != other.abi:
            return False
        if self.api != other.api:
            return False
        if self.toolchain != other.toolchain:
            return False
        if self.force_pie != other.force_pie:
            return False
        return True

    def __str__(self):
        pie_option = 'default-pie'
        if self.force_pie:
            pie_option = 'force-pie'

        return '{}-{}-{}-{}'.format(
            self.abi, self.api, self.toolchain, pie_option)

    def __hash__(self):
        return hash(str(self))

    @staticmethod
    def from_string(config_string):
        """Converts a string into a BuildConfiguration.

        Args:
            config_string: The string format of the test spec.

        Returns:
            TestSpec matching the given string.

        Raises:
            ValueError: The given string could not be matched to a TestSpec.
        """
        abi, _, rest = config_string.partition('-')
        if abi == 'armeabi' and rest.startswith('v7a-'):
            abi += '-v7a'
            _, _, rest = rest.partition('-')
        elif abi == 'arm64' and rest.startswith('v8a-'):
            abi += '-v8a'
            _, _, rest = rest.partition('-')

        api_str, _, rest = rest.partition('-')
        api = int(api_str)

        toolchain, _, rest = rest.partition('-')

        if rest.startswith('default-pie'):
            force_pie = False
            _, _, rest = rest.partition('-')
            _, _, rest = rest.partition('-')
        elif rest.startswith('force-pie'):
            force_pie = True
            _, _, rest = rest.partition('-')
            _, _, rest = rest.partition('-')
        else:
            raise ValueError('Invalid PIE config: {}'.format(config_string))

        return BuildConfiguration(abi, api, toolchain, force_pie)

    def get_extra_ndk_build_flags(self):
        extra_flags = []
        if self.force_pie:
            extra_flags.append('APP_PIE=true')
        extra_flags.append('V=1')
        return extra_flags

    def get_extra_cmake_flags(self):
        extra_flags = []
        if self.force_pie:
            extra_flags.append('-DANDROID_PIE=TRUE')
        extra_flags.append('-DCMAKE_VERBOSE_MAKEFILE=ON')
        return extra_flags
