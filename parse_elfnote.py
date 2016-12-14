#!/usr/bin/env python
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

import argparse
import subprocess
import sys
from ctypes import c_char
from ctypes import c_int
from ctypes import Structure

SEC_NAME = '.note.android.ide'
ABI_VENDOR = 'Android'
NDK_RESERVED_SIZE = 64


class AbiTag(Structure):
    _fields_ = [('namesz', c_int),
                ('descsz', c_int),
                ('type', c_int),
                ('name', c_char * len(ABI_VENDOR)),
                ('android_api', c_int),
                ('ndk_version', c_char * NDK_RESERVED_SIZE),
                ('ndk_build_number', c_char * NDK_RESERVED_SIZE)]


# Get the offset to a section from the output of readelf
def get_section_pos(sec_name, file_path):
    cmd = ['readelf', '--sections', file_path]
    output = subprocess.check_output(cmd)
    lines = output.split('\n')
    for line in lines:
        if sec_name in line:
            sections = line.split()
            if len(sections) < 6 or sec_name not in sections[1]:
                sys.exit('Failed to get offset of {}'.format(sec_name))
            addr = int(sections[3], 16)
            off = int(sections[4], 16)
            return addr + off
    sys.exit('Failed to find section: {}'.format(sec_name))


def print_info(tag):
    print '----------ABI INFO----------'
    print 'ABI_NOTETYPE: {}'.format(tag.type)
    print 'ABI_VENDOR: {}'.format(tag.name)
    print 'ABI_ANDROID_API: {}'.format(tag.android_api)
    print 'ABI_NDK_VERSION: {}'.format(tag.ndk_version)
    print 'ABI_NDK_BUILD_NUMBER: {}'.format(tag.ndk_build_number)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_path',
                        help="path of the ELF file with embedded ABI tags")
    args = parser.parse_args()
    file_path = args.file_path

    with open(file_path, "rb") as obj_file:
        pos = get_section_pos(SEC_NAME, file_path)
        obj_file.seek(pos)
        tag = AbiTag()
        obj_file.readinto(tag)
        print_info(tag)


if __name__ == '__main__':
    main()
