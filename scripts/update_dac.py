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
"""Builds the user documentation and copies it into a DAC tree."""
import argparse
import logging
import os.path
import shutil
import subprocess


THIS_DIR = os.path.realpath(os.path.dirname(__file__))
NDK_DIR = os.path.dirname(THIS_DIR)


def check_call(cmd, *args, **kwargs):
    logging.getLogger(__name__).info('COMMAND: %s', ' '.join(cmd))
    subprocess.check_call(cmd, *args, **kwargs)


def build_docs():
    docs_dir = os.path.join(NDK_DIR, 'docs')
    check_call(['make', '-C', docs_dir])
    return os.path.join(docs_dir, 'html/user')


def copy_docs(docs_tree, docs_out):
    dest_dir = os.path.join(docs_tree, 'frameworks/base/docs/html/ndk/guides')

    for root, _dirs, files in os.walk(docs_out):
        for file_name in files:
            shutil.copy2(os.path.join(root, file_name), dest_dir)
            check_call(['git', '-C', dest_dir, 'add', file_name])


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'docs_tree', type=os.path.realpath, metavar='DOCS_TREE',
        help='Path to DAC tree')

    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    docs_out = build_docs()
    copy_docs(args.docs_tree, docs_out)


if __name__ == '__main__':
    main()
