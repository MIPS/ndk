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
"""Device wrappers and device fleet management."""
import distutils.spawn
import logging
import re
import subprocess

try:
    import adb  # pylint: disable=import-error
except ImportError:
    import site
    from build.lib.build_support import android_path
    site.addsitedir(android_path('development/python-packages'))
    import adb  # pylint: disable=import-error


def logger():
    """Returns the module logger."""
    return logging.getLogger(__name__)


class Device(adb.AndroidDevice):
    """A device to be used for testing."""
    # pylint: disable=super-on-old-class
    # pylint: disable=no-member
    def __init__(self, serial):
        super(Device, self).__init__(serial)
        self._did_cache = False
        self._cached_abis = None
        self._ro_build_characteristics = None
        self._ro_build_id = None
        self._ro_build_version_sdk = None
        self._ro_build_version_codename = None
        self._ro_debuggable = None
        self._ro_product_name = None

    def cache_properties(self):
        """Returns a cached copy of the device's system properties."""
        if not self._did_cache:
            self._ro_build_characteristics = self.get_prop('ro.build.characteristics')
            self._ro_build_id = self.get_prop('ro.build.id')
            self._ro_build_version_sdk = self.get_prop('ro.build.version.sdk')
            self._ro_build_version_codename = self.get_prop('ro.build.version.codename')
            self._ro_debuggable = self.get_prop('ro.debuggable')
            self._ro_product_name = self.get_prop('ro.product.name')
            self._did_cache = True
        return self

    @property
    def name(self):
        return self.cache_properties()._ro_product_name

    @property
    def version(self):
        return int(self.cache_properties()._ro_build_version_sdk)

    @property
    def abis(self):
        """Returns a list of ABIs supported by the device."""
        if self._cached_abis is None:
            # 64-bit devices list their ABIs differently than 32-bit devices. Check
            # all the possible places for stashing ABI info and merge them.
            abi_properties = [
                'ro.product.cpu.abi',
                'ro.product.cpu.abi2',
                'ro.product.cpu.abilist',
            ]
            abis = set()
            for abi_prop in abi_properties:
                value = self.get_prop(abi_prop)
                if value is not None:
                    abis.update(value.split(','))

            _cached_abis = sorted(list(abis))

        return _cached_abis

    @property
    def build_id(self):
        return self.cache_properties()._ro_build_id

    @property
    def is_release(self):
        codename = self.cache_properties()._ro_build_version_codename
        return codename == 'REL'

    @property
    def is_emulator(self):
        chars = self.cache_properties()._ro_build_characteristics
        return chars == 'emulator'

    @property
    def is_debuggable(self):
        return int(self.cache_properties()._ro_debuggable) != 0

    def can_run_build_config(self, config):
        if self.version < config.api:
            # Device is too old for this test.
            return False

        # PIE is enabled by default iff our target version is 16 or newer.
        is_pie = config.force_pie or config.api >= 16
        if not is_pie and self.supports_pie:
            # Don't bother running non-PIE tests on anything that supports PIE.
            return False
        elif is_pie and not self.supports_pie:
            # Can't run PIE on devices older than android-16.
            return False

        if config.abi not in self.abis:
            return False

        return True

    def can_use_asan(self):
        # ASAN is currently only supported for 32-bit ARM and x86...
        asan_abis = {
            'armeabi',
            'armeabi-v7a',
            'x86'
        }

        if not asan_abis.intersection(set(self.abis)):
            logger().info('Cannot use ASAN: no ASAN supported ABIs (%s)',
                          ', '.join(sorted(list(asan_abis))))
            return False

        # On KitKat and newer...
        if self.version < 19:
            logger().info('Cannot use ASAN: device is too old '
                          '(is android-%s, minimum android-19)', self.version)
            return False

        # On rooted devices.
        if not self.is_debuggable:
            logger().info('Cannot use ASAN: device must be rooted')
            return False

        # Fugu's system image doesn't have enough space left for even the ASAN
        # library.
        if self.name == 'fugu':
            logger().info('Cannot use ASAN: system partition full')
            return False

        return True

    @property
    def supports_pie(self):
        return self.version >= 16

    def __str__(self):
        return 'android-{} {} {} {}'.format(
            self.version, self.name, self.serial, self.build_id)

    def __eq__(self, other):
        return self.serial == other.serial


class DeviceFleet(object):
    """A collection of devices that can be used for testing."""
    def __init__(self, test_configurations):
        """Initializes a device fleet.

        Args:
            test_configurations: Dict mapping API levels to a list of ABIs to
                test for that API level. Example:

                    {
                        15: ['armeabi', 'armeabi-v7a'],
                        16: ['armeabi', 'armeabi-v7a', 'x86'],
                    }
        """
        self.devices = {}
        for api, abis in test_configurations.items():
            self.devices[int(api)] = {abi: None for abi in abis}

    def add_device(self, device):
        """Fills a fleet device slot with a device, if appropriate."""
        if device.version not in self.devices:
            logger().info('Ignoring device for unwanted API level: %s', device)
            return

        same_version = self.devices[device.version]
        for abi, current_device in same_version.iteritems():
            # This device can't fulfill this ABI.
            if abi not in device.abis:
                continue

            # Never houdini.
            if abi.startswith('armeabi') and 'x86' in device.abis:
                continue

            # Anything is better than nothing.
            if current_device is None:
                self.devices[device.version][abi] = device
                continue

            # The emulator images have actually been changed over time, so the
            # devices are more trustworthy.
            if current_device.is_emulator and not device.is_emulator:
                self.devices[device.version][abi] = device

            # Trust release builds over pre-release builds, but don't block
            # pre-release because sometimes that's all there is.
            if not current_device.is_release and device.is_release:
                self.devices[device.version][abi] = device

    def get_unique_devices(self):
        devices = set()
        for version in self.get_versions():
            for abi in self.get_abis(version):
                device = self.get_device(version, abi)
                if device is not None:
                    devices.add(device)
        return devices

    def get_device(self, version, abi):
        """Returns the device associated with the given API and ABI."""
        if version not in self.devices:
            return None
        if abi not in self.devices[version]:
            return None
        return self.devices[version][abi]

    def get_missing(self):
        """Describes desired configurations without available deices."""
        missing = []
        for version, abis in self.devices.iteritems():
            for abi, device in abis.iteritems():
                if device is None:
                    missing.append('android-{} {}'.format(version, abi))
        return missing

    def get_versions(self):
        """Returns a list of all API levels in this fleet."""
        return self.devices.keys()

    def get_abis(self, version):
        """Returns a list of all ABIs for the given API level in this fleet."""
        return self.devices[version].keys()


def get_all_attached_devices():
    """Returns a list of all connected devices."""
    if distutils.spawn.find_executable('adb') is None:
        raise RuntimeError('Could not find adb.')

    # We could get the device name from `adb devices -l`, but we need to
    # getprop to find other details anyway, and older devices don't report
    # their names properly (nakasi on android-16, for example).
    p = subprocess.Popen(['adb', 'devices'], stdout=subprocess.PIPE)
    out, _ = p.communicate()
    if p.returncode != 0:
        raise RuntimeError('Failed to get list of devices from adb.')

    # The first line of `adb devices` just says "List of attached devices", so
    # skip that.
    devices = []
    for line in out.split('\n')[1:]:
        if not line.strip():
            continue

        serial, _ = re.split(r'\s+', line, maxsplit=1)

        if 'offline' in line:
            logger().info('Ignoring offline device: %s', serial)
            continue
        if 'unauthorized' in line:
            logger().info('Ignoring unauthorized device: %s', serial)
            continue

        device = Device(serial)
        logger().info('Found device %s', device)
        devices.append(device)

    return devices


def find_devices(sought_devices):
    """Detects connected devices and returns a set for testing.

    We get a list of devices by scanning the output of `adb devices` and
    matching that with the list of desired test configurations specified by
    `sought_devices`.
    """
    fleet = DeviceFleet(sought_devices)
    for device in get_all_attached_devices():
        fleet.add_device(device)

    return fleet
