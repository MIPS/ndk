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
"""Extracts the minSdkVersion from the AndroidManifest.xml file."""
import argparse
import os.path
import xml.etree.ElementTree


def parse_args():
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'manifest_file', metavar='MANIFEST_FILE', type=os.path.abspath,
        help='Path to the AndroidManifest.xml file.')

    return parser.parse_args()


def get_minsdkversion(root):
    """Finds and returns the value of android:minSdkVersion in the manifest.

    Returns:
        String form of android:minSdkVersion if found, else the empty string.
    """
    ns_url = 'http://schemas.android.com/apk/res/android'
    ns = {
        'android': ns_url,
    }

    uses_sdk = root.find('./uses-sdk[@android:minSdkVersion]', ns)
    if uses_sdk is None:
        return ''
    # ElementTree elements don't have the same helpful namespace parameter that
    # the find family does :(
    attrib_name = '{' + ns_url + '}minSdkVersion'
    return uses_sdk.get(attrib_name, '')


def main():
    args = parse_args()

    tree = xml.etree.ElementTree.parse(args.manifest_file)
    print get_minsdkversion(tree.getroot())


if __name__ == '__main__':
    main()
