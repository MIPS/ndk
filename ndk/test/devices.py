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
"""Device wrappers and device fleet management."""
import distutils.spawn
import logging
import re
import subprocess


def logger():
    """Returns the module logger."""
    return logging.getLogger(__name__)


class Device(object):
    """A device to be used for testing."""
    def __init__(self, serial, name, version, build_id, abis, is_emulator):
        self.serial = serial
        self.name = name
        self.version = version
        self.build_id = build_id
        self.abis = abis
        self.is_emulator = is_emulator

    def __str__(self):
        return 'android-{} {} {} {}'.format(
            self.version, self.name, self.serial, self.build_id)


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
            self.devices[api] = {abi: None for abi in abis}

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

    def get_device(self, version, abi):
        """Returns the device associated with the given API and ABI."""
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


def get_device_abis(properties):
    """Returns a list of ABIs supported by the device."""
    # 64-bit devices list their ABIs differently than 32-bit devices. Check all
    # the possible places for stashing ABI info and merge them.
    abi_properties = [
        'ro.product.cpu.abi',
        'ro.product.cpu.abi2',
        'ro.product.cpu.abilist',
    ]
    abis = set()
    for abi_prop in abi_properties:
        if abi_prop in properties:
            abis.update(properties[abi_prop].split(','))

    return sorted(list(abis))


def get_device_details(serial):
    """Returns a Device for the given serial number."""
    import adb  # pylint: disable=import-error
    props = adb.get_device(serial).get_props()
    name = props['ro.product.name']
    version = int(props['ro.build.version.sdk'])
    supported_abis = get_device_abis(props)
    build_id = props['ro.build.id']
    is_emulator = props.get('ro.build.characteristics') == 'emulator'
    return Device(serial, name, version, build_id, supported_abis, is_emulator)


def find_devices(sought_devices):
    """Detects connected devices and returns a set for testing.

    We get a list of devices by scanning the output of `adb devices` and
    matching that with the list of desired test configurations specified by
    `sought_devices`.
    """
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
    fleet = DeviceFleet(sought_devices)
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

        device = get_device_details(serial)
        logger().info('Found device %s', device)
        fleet.add_device(device)

    return fleet
