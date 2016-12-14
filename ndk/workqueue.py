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
import collections
import logging
import multiprocessing
import os
import Queue
import signal
import sys
import traceback


def logger():
    return logging.getLogger(__name__)


def worker_sigterm_handler(_signum, _frame):
    """Raises SystemExit so atexit/finally handlers can be executed."""
    sys.exit()


def _flush_queue(queue):
    """Flushes all pending items from a Queue."""
    try:
        while True:
            queue.get_nowait()
    except Queue.Empty:
        pass


class TaskError(Exception):
    """An error for an exception raised in a worker process.

    Exceptions raised in the worker will not be printed by default, and will
    also not halt execution. We catch these exceptions in the worker process
    and pass them through the queue. Results are checked, and if the result is
    a TaskError the TaskError is raised in the caller's process. The message
    for the TaskError is the stack trace of the original exception, and will be
    printed if the TaskError is not caught.
    """
    def __init__(self, trace):
        super(TaskError, self).__init__(trace)


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
            logger().debug('worker %d waiting for work', os.getpid())
            task = task_queue.get()
            logger().debug('worker %d running task', os.getpid())
            result = task.run()
            logger().debug('worker %d putting result', os.getpid())
            result_queue.put(result)
    except SystemExit:
        pass
    except:  # pylint: disable=bare-except
        logger().debug('worker %d raised exception', os.getpid())
        trace = ''.join(traceback.format_exception(*sys.exc_info()))
        result_queue.put(TaskError(trace))
    finally:
        # multiprocessing.Process.terminate() doesn't kill our descendents.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        logger().debug('worker %d killing process group', os.getpid())
        os.kill(0, signal.SIGTERM)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
    logger().debug('worker %d exiting', os.getpid())


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


class ProcessPoolWorkQueue(object):
    """A pool of processes for executing work asynchronously."""

    join_timeout = 8  # Timeout for join before trying SIGKILL.

    def __init__(self, num_workers=multiprocessing.cpu_count()):
        """Creates a WorkQueue.

        Worker threads are spawned immediately and remain live until both
        terminate() and join() are called.

        Args:
            num_workers: Number of worker processes to spawn.
        """
        if sys.platform == 'win32':
            # TODO(danalbert): Port ProcessPoolWorkQueue to Windows.
            # Our implementation of ProcessPoolWorkQueue depends on process
            # groups, which are not supported on Windows.
            raise NotImplementedError

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
        if type(result) == TaskError:
            raise result
        self.num_tasks -= 1
        return result

    def terminate(self):
        """Terminates all worker processes."""
        for worker in self.workers:
            logger().debug('terminating %d', worker.pid)
            worker.terminate()
        self._flush()

    def _flush(self):
        """Flushes all pending tasks and results.

        If there are still items pending in the queues when terminate is
        called, the subsequent join will hang waiting for the queues to be
        emptied.

        We call _flush after all workers have been terminated to ensure that we
        can exit cleanly.
        """
        _flush_queue(self.task_queue)
        _flush_queue(self.result_queue)

    def join(self):
        """Waits for all worker processes to exit."""
        for worker in self.workers:
            logger().debug('joining %d', worker.pid)
            worker.join(self.join_timeout)
            if worker.is_alive():
                logger().error(
                    'worker %d will not die; sending SIGKILL', worker.pid)
                os.killpg(worker.pid, signal.SIGKILL)
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


class DummyWorkQueue(object):
    """A fake WorkQueue that does not parallelize.

    Useful for debugging when trying to determine if an issue is being caused
    by multiprocess specific behavior.
    """
    def __init__(self):
        """Creates a SerialWorkQueue."""
        self.task_queue = collections.deque()

    def add_task(self, func, *args, **kwargs):
        """Queues up a new task for execution.

        Tasks are executed when get_result is called.

        Args:
            func: An invocable object to be executed by a worker process.
            args: Arguments to be passed to the task.
            kwargs: Keyword arguments to be passed to the task.
        """
        self.task_queue.append(Task(func, args, kwargs))

    def get_result(self):
        """Executes a task and returns the result."""
        task = self.task_queue.popleft()
        try:
            return task.run()
        except:
            trace = ''.join(traceback.format_exception(*sys.exc_info()))
            raise TaskError(trace)

    def terminate(self):
        """Does nothing."""
        pass

    def join(self):
        """Does nothing."""
        pass

    def finished(self):
        """Returns True if all tasks have completed execution."""
        return len(self.task_queue) == 0


if sys.platform == 'win32':
    WorkQueue = DummyWorkQueue
else:
    WorkQueue = ProcessPoolWorkQueue
