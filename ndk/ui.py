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
"""UI classes for build output."""
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import time

import ndk.ansi


class UiRenderer(object):
    def __init__(self, console):
        self.console = console

    def clear_last_render(self):
        raise NotImplementedError

    def render(self, lines):
        raise NotImplementedError


class AnsiUiRenderer(UiRenderer):
    def __init__(self, console):
        super(AnsiUiRenderer, self).__init__(console)
        self.last_rendered_lines = []

    def get_ui_lines(self):
        raise NotImplementedError

    def changed_lines(self, new_lines):
        assert len(new_lines) == len(self.last_rendered_lines)
        old_lines = self.last_rendered_lines
        for idx, (old_line, new_line) in enumerate(zip(old_lines, new_lines)):
            if old_line != new_line:
                yield idx, new_line

    def clear_last_render(self):
        self.console.clear_lines(len(self.last_rendered_lines))
        self.last_rendered_lines = []

    def render(self, lines):
        if not self.last_rendered_lines:
            self.console.print(os.linesep.join(lines), end='')
        else:
            redraw_commands = []
            last_idx = 0
            for idx, new_line in self.changed_lines(lines):
                redraw_commands.append(ndk.ansi.cursor_down(idx - last_idx))
                redraw_commands.append(ndk.ansi.goto_first_column())
                redraw_commands.append(ndk.ansi.clear_line())
                redraw_commands.append(new_line)
                last_idx = idx
            if redraw_commands:
                total_lines = len(self.last_rendered_lines)
                goto_top = ndk.ansi.cursor_up(total_lines - 1)
                goto_bottom = ndk.ansi.cursor_down(total_lines - last_idx)
                self.console.print(
                    goto_top + ''.join(redraw_commands) + goto_bottom,
                    end='')
        self.last_rendered_lines = lines


class DumbUiRenderer(UiRenderer):
    def __init__(self, console, redraw_rate=30):
        super(DumbUiRenderer, self).__init__(console)
        self.redraw_rate = redraw_rate
        self.last_draw = None

    def clear_last_render(self):
        pass

    def ready_for_draw(self):
        if self.last_draw is None:
            return True

        current_time = time.time()
        if current_time - self.last_draw >= self.redraw_rate:
            return True

        return False

    def render(self, lines):
        if not self.ready_for_draw():
            return

        self.console.print(os.linesep.join(lines))
        sys.stdout.flush()
        self.last_draw = time.time()


class Ui(object):
    def __init__(self, ui_renderer):
        self.ui_renderer = ui_renderer

    def get_ui_lines(self):
        raise NotImplementedError

    def clear(self):
        self.ui_renderer.clear_last_render()

    def draw(self):
        self.ui_renderer.render(self.get_ui_lines())
