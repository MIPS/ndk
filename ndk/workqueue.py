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
"""Defines WorkQueue for delegating asynchronous work to subprocesses."""
import multiprocessing
import os
import signal
import sys


def worker_sigterm_handler(_signum, _frame):
    """Raises SystemExit so atexit/finally handlers can be executed."""
    sys.exit()


def worker_main(task_queue, result_queue):
    """Main loop for worker processes.

    Args:
        task_queue: A multiprocessing.Queue of Tasks to retrieve work from.
        result_queue: A multiprocessing.Queue to push results to.
    """
    os.setpgrp()
    signal.signal(signal.SIGTERM, worker_sigterm_handler)
    try:
        while True:
            task = task_queue.get()
            result = task.run()
            result_queue.put(result)
    finally:
        # multiprocessing.Process.terminate() doesn't kill our descendents.
        os.kill(0, signal.SIGTERM)


class Task(object):
    """A task to be executed by a worker process."""
    def __init__(self, func, args, kwargs):
        """Creates a task.

        Args:
            func: An invocable object to be executed by a worker process.
            args: Arguments to be passed to the task.
            kwargs: Keyword arguments to be passed to the task.
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Invokes the task."""
        return self.func(*self.args, **self.kwargs)


class WorkQueue(object):
    """A pool of processes for executing work asynchronously."""
    def __init__(self, num_workers):
        """Creates a WorkQueue.

        Worker threads are spawned immediately and remain live until both
        terminate() and join() are called.

        Args:
            num_workers: Number of worker processes to spawn.
        """
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.workers = []
        # multiprocessing.JoinableQueue's join isn't able to implement
        # finished() because it doesn't come in a non-blocking flavor.
        self.num_tasks = 0
        self._spawn_workers(num_workers)

    def add_task(self, func, *args, **kwargs):
        """Queues up a new task for execution.

        Tasks are executed in order of insertion as worker processes become
        available.

        Args:
            func: An invocable object to be executed by a worker process.
            args: Arguments to be passed to the task.
            kwargs: Keyword arguments to be passed to the task.
        """
        self.task_queue.put(Task(func, args, kwargs))
        self.num_tasks += 1

    def get_result(self):
        """Gets a result from the queue, blocking until one is available."""
        result = self.result_queue.get()
        self.num_tasks -= 1
        return result

    def terminate(self):
        """Terminates all worker processes."""
        for worker in self.workers:
            worker.terminate()

    def join(self):
        """Waits for all worker processes to exit."""
        for worker in self.workers:
            worker.join()
        self.workers = []

    def finished(self):
        """Returns True if all tasks have completed execution."""
        return self.num_tasks == 0

    def _spawn_workers(self, num_workers):
        """Spawns the worker processes.

        Args:
            num_workers: Number of worker proceeses to spawn.
        """
        for _ in range(num_workers):
            worker = multiprocessing.Process(
                target=worker_main, args=(self.task_queue, self.result_queue))
            worker.start()
            self.workers.append(worker)
