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
"""ANSI terminal control."""
from __future__ import absolute_import
from __future__ import print_function

import contextlib
import os
import sys

try:
    import termios
    HAVE_TERMIOS = True
except ImportError:
    HAVE_TERMIOS = False


def cursor_up(lines):
    # \033[0A still goes up one line. Emit nothing.
    if lines == 0:
        return ''
    return '\033[{}A'.format(lines)


def cursor_down(lines):
    # \033[0B still goes down one line. Emit nothing.
    if lines == 0:
        return ''
    return '\033[{}B'.format(lines)


def goto_first_column():
    return '\033[1G'


def clear_line():
    return '\033[K'


def is_self_in_tty_foreground_group(fd):
    """Is this process in the foreground process group of a tty identified
    by fd?"""
    return HAVE_TERMIOS and fd.isatty() and \
        os.getpgrp() == os.tcgetpgrp(fd.fileno())


@contextlib.contextmanager
def disable_terminal_echo(fd):
    # If we call tcsetattr from a background process group, it will suspend
    # this process.
    if is_self_in_tty_foreground_group(fd):
        original = termios.tcgetattr(fd)
        termattr = termios.tcgetattr(fd)
        termattr[3] &= ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, termattr)
        try:
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSANOW, original)
    else:
        yield


def get_console(stream=sys.stdout):
    if stream.isatty() and os.name != 'nt':
        return AnsiConsole(stream)
    else:
        return DumbConsole(stream)


class Console(object):
    def __init__(self, stream):
        self.stream = stream

    def print(self, *args, **kwargs):
        print(*args, file=self.stream, **kwargs)
        self.stream.flush()

    @contextlib.contextmanager
    def cursor_hide_context(self):
        self.hide_cursor()
        try:
            yield
        finally:
            self.show_cursor()

    def clear_lines(self, num_lines):
        raise NotImplementedError

    def hide_cursor(self):
        raise NotImplementedError

    def show_cursor(self):
        raise NotImplementedError


class AnsiConsole(Console):
    GOTO_HOME = '\r'
    CURSOR_UP = '\033[1A'
    CLEAR_LINE = '\033[K'
    HIDE_CURSOR = '\033[?25l'
    SHOW_CURSOR = '\033[?25h'

    def __init__(self, stream):
        super(AnsiConsole, self).__init__(stream)
        self.smart_console = True

    def _do(self, cmd):
        print(cmd, end='', file=self.stream)
        self.stream.flush()

    def clear_lines(self, num_lines):
        """Clears num_lines lines and positions the cursor at the top left."""
        cmds = [self.GOTO_HOME]
        for idx in range(num_lines):
            # For the first line, we're already in place.
            if idx != 0:
                cmds.append(self.CURSOR_UP)
            cmds.append(self.CLEAR_LINE)
        self._do(''.join(cmds))

    def hide_cursor(self):
        self._do(self.HIDE_CURSOR)

    def show_cursor(self):
        self._do(self.SHOW_CURSOR)


class DumbConsole(Console):
    def __init__(self, stream):
        super(DumbConsole, self).__init__(stream)
        self.smart_console = False

    def clear_lines(self, _num_lines):
        pass

    def hide_cursor(self):
        pass

    def show_cursor(self):
        pass
