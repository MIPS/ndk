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
"""Tests for ndk.test.devices."""
from __future__ import absolute_import

import unittest

import ndk.test.devices
import ndk.test.spec


class MockDevice(ndk.test.devices.Device):
    def __init__(self, version, abis):  # pylint: disable=super-on-old-class
        super(MockDevice, self).__init__('')
        self._version = version
        self._abis = abis

    @property
    def abis(self):
        return self._abis

    @property
    def version(self):
        return self._version


class MockConfig(ndk.test.spec.BuildConfiguration):
    def __init__(self, abi, api, force_pie):
        super(MockConfig, self).__init__(
            abi, api, 'clang', force_pie, False, False)


class DeviceTest(unittest.TestCase):
    def test_can_run_build_config(self):
        ics_arm = MockDevice(15, ['armeabi', 'armeabi-v7a'])
        jb_arm = MockDevice(16, ['armeabi', 'armeabi-v7a'])
        n_arm = MockDevice(25, ['armeabi', 'armeabi-v7a', 'arm64-v8a'])
        n_intel = MockDevice(25, ['x86', 'x86_64'])

        ics_arm5_default_pie = MockConfig('armeabi', 14, False)
        self.assertTrue(ics_arm.can_run_build_config(ics_arm5_default_pie))
        # Non-PIE supported, but we run the PIE executables instead.
        self.assertFalse(jb_arm.can_run_build_config(ics_arm5_default_pie))
        # Requires PIE.
        self.assertFalse(n_arm.can_run_build_config(ics_arm5_default_pie))
        # Wrong ABI.
        self.assertFalse(n_intel.can_run_build_config(ics_arm5_default_pie))

        ics_arm7_default_pie = MockConfig('armeabi-v7a', 14, False)
        self.assertTrue(ics_arm.can_run_build_config(ics_arm7_default_pie))
        # Non-PIE supported, but we run the PIE executables instead.
        self.assertFalse(jb_arm.can_run_build_config(ics_arm7_default_pie))
        # Requires PIE.
        self.assertFalse(n_arm.can_run_build_config(ics_arm7_default_pie))
        # Wrong ABI.
        self.assertFalse(n_intel.can_run_build_config(ics_arm7_default_pie))

        ics_arm7_force_pie = MockConfig('armeabi-v7a', 14, True)
        # No PIE support.
        self.assertFalse(ics_arm.can_run_build_config(ics_arm7_force_pie))
        self.assertTrue(jb_arm.can_run_build_config(ics_arm7_force_pie))
        self.assertTrue(n_arm.can_run_build_config(ics_arm7_force_pie))
        # Wrong ABI.
        self.assertFalse(n_intel.can_run_build_config(ics_arm7_force_pie))

        jb_arm7_default_pie = MockConfig('armeabi-v7a', 16, False)
        # Too old, no PIE support.
        self.assertFalse(ics_arm.can_run_build_config(jb_arm7_default_pie))
        self.assertTrue(jb_arm.can_run_build_config(jb_arm7_default_pie))
        self.assertTrue(n_arm.can_run_build_config(jb_arm7_default_pie))
        # Wrong ABI.
        self.assertFalse(n_intel.can_run_build_config(jb_arm7_default_pie))

        l_arm7_default_pie = MockConfig('armeabi-v7a', 21, False)
        # Too old, no PIE support.
        self.assertFalse(ics_arm.can_run_build_config(l_arm7_default_pie))
        # Too old.
        self.assertFalse(jb_arm.can_run_build_config(l_arm7_default_pie))
        self.assertTrue(n_arm.can_run_build_config(l_arm7_default_pie))
        # Wrong ABI.
        self.assertFalse(n_intel.can_run_build_config(l_arm7_default_pie))

        l_arm64_default_pie = MockConfig('arm64-v8a', 21, False)
        # Too old, no PIE support, wrong ABI.
        self.assertFalse(ics_arm.can_run_build_config(l_arm64_default_pie))
        # Too old, wrong ABI.
        self.assertFalse(jb_arm.can_run_build_config(l_arm64_default_pie))
        self.assertTrue(n_arm.can_run_build_config(l_arm64_default_pie))
        # Wrong ABI.
        self.assertFalse(n_intel.can_run_build_config(l_arm64_default_pie))

        l_intel_default_pie = MockConfig('x86_64', 21, False)
        # Too old, no PIE support, wrong ABI.
        self.assertFalse(ics_arm.can_run_build_config(l_intel_default_pie))
        # Too old, wrong ABI.
        self.assertFalse(jb_arm.can_run_build_config(l_intel_default_pie))
        # Wrong ABI.
        self.assertFalse(n_arm.can_run_build_config(l_intel_default_pie))
        self.assertTrue(n_intel.can_run_build_config(l_intel_default_pie))

        o_arm7_default_pie = MockConfig('armeabi-v7a', 26, False)
        # Too old, no PIE support.
        self.assertFalse(ics_arm.can_run_build_config(o_arm7_default_pie))
        # Too old.
        self.assertFalse(jb_arm.can_run_build_config(o_arm7_default_pie))
        # Too old.
        self.assertFalse(n_arm.can_run_build_config(o_arm7_default_pie))
        # Too old, wrong ABI.
        self.assertFalse(n_intel.can_run_build_config(o_arm7_default_pie))

        o_arm64_default_pie = MockConfig('arm64-v8a', 26, False)
        # Too old, no PIE support.
        self.assertFalse(ics_arm.can_run_build_config(o_arm64_default_pie))
        # Too old.
        self.assertFalse(jb_arm.can_run_build_config(o_arm64_default_pie))
        # Too old.
        self.assertFalse(n_arm.can_run_build_config(o_arm64_default_pie))
        # Too old, wrong ABI.
        self.assertFalse(n_intel.can_run_build_config(o_arm64_default_pie))

        o_intel_default_pie = MockConfig('x86_64', 26, False)
        # Too old, no PIE support, wrong ABI.
        self.assertFalse(ics_arm.can_run_build_config(o_intel_default_pie))
        # Too old, wrong ABI.
        self.assertFalse(jb_arm.can_run_build_config(o_intel_default_pie))
        # Too old, wrong ABI.
        self.assertFalse(n_arm.can_run_build_config(o_intel_default_pie))
        # Too old.
        self.assertFalse(n_intel.can_run_build_config(o_intel_default_pie))
