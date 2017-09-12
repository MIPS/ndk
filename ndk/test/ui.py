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
"""UI classes for test output."""
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import time

import ndk.ansi


def get_test_progress_renderer(console):
    if console.smart_console:
        return AnsiTestProgressRenderer(console)
    else:
        return DumbTestProgressRenderer(console)


class TestProgressRenderer(object):
    NUM_TESTS_DIGITS = 6

    def __init__(self, console):
        self.console = console

    def make_status_lines(self, workqueue):  # pylint: disable=no-self-use
        lines = []
        lines.append('{: >{width}} tests remaining'.format(
            workqueue.num_tasks, width=self.NUM_TESTS_DIGITS))
        for group in sorted(workqueue.task_queues.keys()):
            group_id = '{} devices android-{} {}'.format(
                len(group.devices), group.devices[0].version,
                ', '.join(group.abis))
            lines.append('{: >{width}} {}'.format(
                workqueue.task_queues[group].qsize(), group_id,
                width=self.NUM_TESTS_DIGITS))
        return lines

    def clear_last_render(self):
        raise NotImplementedError

    def render(self, workqueue):
        raise NotImplementedError


class AnsiTestProgressRenderer(TestProgressRenderer):
    def __init__(self, console):
        super(AnsiTestProgressRenderer, self).__init__(console)
        self.last_rendered_lines = []

    def changed_lines(self, new_lines):
        assert len(new_lines) == len(self.last_rendered_lines)
        old_lines = self.last_rendered_lines
        for idx, (old_line, new_line) in enumerate(zip(old_lines, new_lines)):
            if old_line != new_line:
                yield idx, new_line

    def make_status_lines(self, workqueue):
        lines = super(AnsiTestProgressRenderer, self).make_status_lines(
            workqueue)
        worker_status_lines = []
        for work_queue in workqueue.work_queues:
            for worker in work_queue.workers:
                worker_status_lines.append(worker.status)
        return worker_status_lines + lines

    def clear_last_render(self):
        self.console.clear_lines(len(self.last_rendered_lines))
        self.last_rendered_lines = []

    def render(self, workqueue):
        lines = self.make_status_lines(workqueue)
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


class DumbTestProgressRenderer(TestProgressRenderer):
    def __init__(self, console, redraw_rate=30):
        super(DumbTestProgressRenderer, self).__init__(console)
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

    def render(self, workqueue):
        if not self.ready_for_draw():
            return

        self.console.print(os.linesep.join(self.make_status_lines(workqueue)))
        sys.stdout.flush()
        self.last_draw = time.time()
