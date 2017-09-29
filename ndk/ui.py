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
    # Number of seconds to delay between each draw command when debugging.
    debug_draw_delay = 0.1

    def __init__(self, console, debug_draw=False):
        super(AnsiUiRenderer, self).__init__(console)
        self.last_rendered_lines = []
        self.debug_draw = debug_draw

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

    def draw(self, commands):
        if self.debug_draw:
            for cmd in commands:
                self.console.print(cmd, end='')
                time.sleep(self.debug_draw_delay)
        else:
            self.console.print(''.join(commands), end='')

    def render(self, lines):
        if not self.last_rendered_lines:
            self.console.print(os.linesep.join(lines), end='')
        elif len(lines) != len(self.last_rendered_lines):
            self.clear_last_render()
            self.render(lines)
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
                goto_bottom = ndk.ansi.cursor_down(total_lines - last_idx - 1)

                self.draw([goto_top] + redraw_commands + [goto_bottom])

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


def get_build_progress_ui(console, workqueue):
    if console.smart_console:
        ui_renderer = AnsiUiRenderer(console)
        return BuildProgressUi(ui_renderer, workqueue)
    else:
        return DumbBuildProgressUi()


class BuildProgressUi(Ui):
    def __init__(self, ui_renderer, workqueue):
        super(BuildProgressUi, self).__init__(ui_renderer)
        self.workqueue = workqueue

    def get_ui_lines(self):
        lines = []
        for worker in self.workqueue.workers:
            status = worker.status
            if status != worker.IDLE_STATUS:
                lines.append(status)
        return lines


class DumbBuildProgressUi(object):
    def clear(self):
        pass

    def draw(self):
        # Don't flood the terminal with repeated status of what is still
        # building. it will be printing the same three modules for most of the
        # build.
        pass


def get_work_queue_ui(console, workqueue):
    if console.smart_console:
        ui_renderer = ndk.ui.AnsiUiRenderer(console)
        show_worker_status = True
    else:
        ui_renderer = ndk.ui.DumbUiRenderer(console)
        show_worker_status = False
    return WorkQueueUi(
        ui_renderer, show_worker_status, workqueue)


class WorkQueueUi(Ui):
    NUM_TESTS_DIGITS = 6

    def __init__(self, ui_renderer, show_worker_status, workqueue):
        super(WorkQueueUi, self).__init__(ui_renderer)
        self.show_worker_status = show_worker_status
        self.workqueue = workqueue

    def get_ui_lines(self):
        lines = []

        if self.show_worker_status:
            for worker in self.workqueue.workers:
                lines.append(worker.status)

        lines.append('{: >{width}} jobs remaining'.format(
            self.workqueue.num_tasks, width=self.NUM_TESTS_DIGITS))
        return lines
