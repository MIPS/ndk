#
# Copyright (C) 2018 The Android Open Source Project
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
"""Check for correct link order from ndk-build.
"""
import difflib
import os
import re
import shlex
import subprocess
import sys


def is_linked_item(arg):
    """Returns True if the argument is an object or library to be linked."""
    if arg.endswith('.a'):
        return True
    if arg.endswith('.o'):
        return True
    if arg.endswith('.so'):
        return True
    if arg.startswith('-l'):
        return True
    return False


def find_link_args(link_line):
    """Returns a list of objects and libraries in the link command."""
    args = []

    # A trivial attempt at parsing here is fine since we can assume that all
    # our objects and libraries will not include spaces and we don't care about
    # the rest of the arguments.
    #
    # Arguments could be quoted on Windows. shlex.split should be good enough:
    # "C:/src/android-ndk-r17-beta1/build//../platforms/android-21/arch-x86_64/usr/lib/../lib64\\crtbegin_so.o"
    skip_next = False
    for word in shlex.split(link_line):
        if skip_next:
            skip_next = False
            continue
        if word in ('-o', '-soname', '--exclude-libs'):
            skip_next = True
            continue

        if is_linked_item(word):
            # Use just the base name so we can compare to an exact expected
            # link order regardless of ABI.
            if os.sep in word or (os.altsep and os.altsep in word):
                word = os.path.basename(word)
            args.append(word)
    return args


def check_link_order(link_line, abi, api):
    """Determines if a given link command has the correct ordering.

    Args:
        link_line (string): The full ld command.

    Returns:
        Tuple of (success, diff). The diff will be None on success or a
        difflib.unified_diff result with no line terminations, i.e. a generator
        suitable for use with `' '.join()`. The diff represents the changes
        between the expected link order and the actual link order.
    """
    libunwind_arg = ['libunwind.a'] if abi == 'armeabi-v7a' else []
    android_support_arg = ['libandroid_support.a'] if api < 21 else []
    expected = [
        'crtbegin_so.o',
        'foo.o',
    ] + android_support_arg + libunwind_arg + [
        # The most important part of this test is checking that libgcc comes
        # *before* the shared libraries so we can be sure we're actually
        # getting libgcc symbols rather than getting them from some shared
        # library dependency that's re-exporting them.
        '-lgcc',
        '-latomic',
        'libc++_shared.so',
        '-lc',
        '-lm',
        '-lm',
        '-lgcc',
        '-ldl',
        '-lc',
        '-lgcc',
        '-ldl',
        'crtend_so.o',
    ]
    link_args = find_link_args(link_line)
    if link_args == expected:
        return True, None
    return False, difflib.unified_diff(expected, link_args, lineterm='')


def run_test(ndk_path, abi, platform, _toolchain, build_flags):
    """Checks clang's -v output for proper link ordering."""
    ndk_build = os.path.join(ndk_path, 'ndk-build')
    if sys.platform == 'win32':
        ndk_build += '.cmd'
    project_path = 'project'
    ndk_args = build_flags + [
        'APP_ABI=' + abi,
        'APP_PLATFORM=android-{}'.format(platform),
    ]
    proc = subprocess.Popen([ndk_build, '-C', project_path] + ndk_args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = proc.communicate()
    if proc.returncode != 0:
        return proc.returncode == 0, out

    link_line = None
    for line in out.splitlines():
        if 'bin/ld' in re.sub(r'[/\\]+', '/', line):
            if link_line is not None:
                err_msg = 'Found duplicate link lines:\n{}\n{}'.format(
                    link_line, line)
                return False, err_msg
            else:
                link_line = line

    if link_line is None:
        return False, 'Did not find link line in out:\n{}'.format(out)

    result, diff = check_link_order(link_line, abi, platform)
    return result, '' if diff is None else os.linesep.join(diff)
