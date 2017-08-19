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
import logging
import subprocess
import sys
from ctypes import c_char
from ctypes import c_int
from ctypes import Structure

SEC_NAME = '.note.android.ident'
ABI_VENDOR = 'Android'
NDK_RESERVED_SIZE = 64


def logger():
    """Returns the module logger."""
    return logging.getLogger(__name__)


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
    cmd = ['readelf', '--sections', '-W', file_path]
    output = subprocess.check_output(cmd)
    lines = output.split('\n')
    for line in lines:
        logger().debug('Checking line for "%s": %s', sec_name, line)
        # Looking for a line like the following (all whitespace of unknown
        # width).
        #
        #   [ 8] .note.android.ident NOTE 00000000 0000ec 000098 00 A 0 0 4
        #
        # The only column that might have internal whitespace is the first one.
        # Since we don't care about it, remove the head of the string until the
        # closing bracket, then split.
        if sec_name not in line:
            continue
        if ']' not in line:
            continue
        line = line[line.index(']') + 1:].strip()

        sections = line.split()
        if len(sections) < 5 or sec_name not in sections[0]:
            logger().debug('Did not find "%s" in %s', sec_name, sections[0])
            sys.exit('Failed to get offset of {}'.format(sec_name))
        addr = int(sections[2], 16)
        off = int(sections[3], 16)
        return off
    sys.exit('Failed to find section: {}'.format(sec_name))


def print_info(tag):
    print '----------ABI INFO----------'
    print 'ABI_NOTETYPE: {}'.format(tag.type)
    print 'ABI_VENDOR: {}'.format(tag.name)
    print 'ABI_ANDROID_API: {}'.format(tag.android_api)
    print 'ABI_NDK_VERSION: {}'.format(tag.ndk_version)
    print 'ABI_NDK_BUILD_NUMBER: {}'.format(tag.ndk_build_number)


def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('file_path',
                        help="path of the ELF file with embedded ABI tags")
    parser.add_argument(
        '-v', '--verbose', dest='verbosity', action='count', default=0,
        help='Increase logging verbosity.')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbosity >= 2:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    file_path = args.file_path

    with open(file_path, "rb") as obj_file:
        pos = get_section_pos(SEC_NAME, file_path)
        obj_file.seek(pos)
        tag = AbiTag()
        obj_file.readinto(tag)
        print_info(tag)


if __name__ == '__main__':
    main()
