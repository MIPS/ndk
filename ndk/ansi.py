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

    @contextlib.contextmanager
    def cursor_hide_context(self):
        self.hide_cursor()
        yield
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
        cmds = []
        for _ in range(num_lines):
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
