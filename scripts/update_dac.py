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

"""Builds the docs/user documentation and copies it into a DAC tree.

To use (inside Google):

g4 citc update-dac
$NDK/scripts/update_dac.py /google/src/cloud/$USER/update-dac/google3
cd /google/src/cloud/$USER/update-dac/google3
g4 mail
"""

import argparse
import logging
import os


THIS_DIR = os.path.realpath(os.path.dirname(__file__))
NDK_DIR = os.path.dirname(THIS_DIR)


def logger():
    """Get the module logger."""
    return logging.getLogger(__name__)


def copy2(src, dst):
    """shutil.copy2 with logging."""
    import shutil
    logger().info('copy2: %s %s', src, dst)
    shutil.copy2(src, dst)


def rmtree(path):
    """shutil.rmtree with logging."""
    import shutil
    logger().info('rmtree: %s', path)
    shutil.rmtree(path)


def makedirs(path):
    """os.makedirs with logging."""
    logger().info('makedirs: %s', path)
    os.makedirs(path)


def call(cmd, *args, **kwargs):
    """subprocess.call with logging."""
    import subprocess
    logger().info('call: %s', ' '.join(cmd))
    subprocess.call(cmd, *args, **kwargs)


def build_docs():
    """Perform any necessary preprocessing steps.

    * Rewrite "[TOC]" (gitiles spelling) to "[[TOC]]" (devsite spelling).
    * Add devsite metadata for navigation support.
    """
    docs_dir = os.path.join(NDK_DIR, 'docs/user')
    out_dir = os.path.join(NDK_DIR, 'docs/out')
    if os.path.exists(out_dir):
        rmtree(out_dir)
    makedirs(out_dir)
    for doc in os.listdir(docs_dir):
        with open(os.path.join(out_dir, doc), 'w') as out_file:
            out_file.write(
                'Project: /ndk/_project.yaml\n'
                'Book: /ndk/guides/_book.yaml\n'
                'Subcategory: guide\n'
                '\n')

            path = os.path.join(docs_dir, doc)
            with open(path) as in_file:
                contents = in_file.read()
                contents = contents.replace('[TOC]', '[[TOC]]')
                out_file.write(contents)
    return out_dir


def copy_docs(docs_tree, docs_out):
    """Copy the docs to the devsite directory."""
    dest_dir = os.path.join(
        docs_tree, 'googledata/devsite/site-android/en/ndk/guides')

    cwd = os.getcwd()
    for root, _, files in os.walk(docs_out):
        for file_name in files:
            dest_path = os.path.join(dest_dir, file_name)
            if os.path.exists(dest_path):
                # `g4 edit` doesn't work unless it's actually in the citc
                # client.
                os.chdir(dest_dir)
                try:
                    # Might fail if the file is new (will only happen if the
                    # script is re-run), but that's not a problem.
                    call(['g4', 'edit', file_name])
                finally:
                    os.chdir(cwd)
            copy2(os.path.join(root, file_name), dest_dir)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'docs_tree', type=os.path.realpath, metavar='DOCS_TREE',
        help='Path to DAC tree')

    return parser.parse_args()


def main():
    """Program entry point."""
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    docs_out = build_docs()
    copy_docs(args.docs_tree, docs_out)


if __name__ == '__main__':
    main()
