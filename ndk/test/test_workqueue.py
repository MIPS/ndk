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
"""Tests for ndk.workqueue."""
import multiprocessing
import os
import signal
import sys
import time
import unittest

import ndk.workqueue


def put(_worker, i):
    """Returns an the passed argument."""
    return i


class Functor(object):
    """Functor that returns the argument passed to the constructor."""
    def __init__(self, value):
        self.value = value

    def __call__(self, _worker):
        return self.value


def block_on_event(_worker, event):
    """Blocks until the event is signalled."""
    event.wait()


def update_status(worker, ready_event, finish_event, new_status):
    """Updates the worker's status and waits for an event before finishing."""
    worker.status = new_status
    ready_event.set()
    finish_event.wait()


def sigterm_handler(_signum, _trace):
    """Raises SystemExit."""
    sys.exit()


def sleep_until_sigterm(pid_queue):
    """Sleeps until signalled, then passes the PID through the queue."""
    signal.signal(signal.SIGTERM, sigterm_handler)
    try:
        while True:
            time.sleep(60)  # There is no signal.pause() on Windows :(
    finally:
        pid_queue.put(os.getpid())


def spawn_child(_worker, pid_queue):
    """Spawns a child process to check behavior of terminate().

    The PIDs of both processes are returned via the pid_queue, and then both
    processes go to sleep. SIGTERM will be caught by both processes, and the
    PIDs will be passed through the queue again to inform the caller that both
    processes were signalled.
    """
    os.fork()
    pid_queue.put(os.getpid())
    sleep_until_sigterm(pid_queue)


def raise_error():
    """Raises a RuntimeError to be re-raised in the caller."""
    raise RuntimeError('Error in child')


class WorkQueueTest(unittest.TestCase):
    """Tests for WorkQueue."""
    def test_put_func(self):
        """Test that we can pass a function to the queue and get results."""
        workqueue = ndk.workqueue.WorkQueue(4)

        workqueue.add_task(put, 1)
        workqueue.add_task(put, 2)
        expected_results = [1, 2]

        while expected_results:
            i = workqueue.get_result()
            self.assertIn(i, expected_results)
            expected_results.remove(i)

        workqueue.terminate()
        workqueue.join()

    def test_put_functor(self):
        """Test that we can pass a functor to the queue and get results."""
        workqueue = ndk.workqueue.WorkQueue(4)

        workqueue.add_task(Functor(1))
        workqueue.add_task(Functor(2))
        expected_results = [1, 2]

        while expected_results:
            i = workqueue.get_result()
            self.assertIn(i, expected_results)
            expected_results.remove(i)

        workqueue.terminate()
        workqueue.join()

    def test_finished(self):
        """Tests that finished() returns the correct result."""
        workqueue = ndk.workqueue.WorkQueue(4)
        self.assertTrue(workqueue.finished())

        manager = multiprocessing.Manager()
        event = manager.Event()
        workqueue.add_task(block_on_event, event)
        self.assertFalse(workqueue.finished())
        event.set()
        workqueue.get_result()
        self.assertTrue(workqueue.finished())

        workqueue.terminate()
        workqueue.join()
        self.assertTrue(workqueue.finished())

    def test_status(self):
        """Tests that worker status can be accessed from the parent."""
        workqueue = ndk.workqueue.WorkQueue(1)

        manager = multiprocessing.Manager()
        ready_event = manager.Event()
        finish_event = manager.Event()
        self.assertEqual(
            ndk.workqueue.Worker.IDLE_STATUS, workqueue.workers[0].status)
        workqueue.add_task(update_status, ready_event, finish_event, 'working')
        ready_event.wait()
        self.assertEqual('working', workqueue.workers[0].status)
        finish_event.set()
        workqueue.get_result()
        self.assertEqual(
            ndk.workqueue.Worker.IDLE_STATUS, workqueue.workers[0].status)

        workqueue.terminate()
        workqueue.join()

    def test_subprocesses_killed(self):
        """Tests that terminate() kills descendents of worker processes."""
        workqueue = ndk.workqueue.WorkQueue(4)

        manager = multiprocessing.Manager()
        queue = manager.Queue()

        workqueue.add_task(spawn_child, queue)
        pids = []
        pids.append(queue.get())
        pids.append(queue.get())
        workqueue.terminate()
        workqueue.join()

        killed_pid = queue.get()
        self.assertIn(killed_pid, pids)
        pids.remove(killed_pid)

        killed_pid = queue.get()
        self.assertIn(killed_pid, pids)
        pids.remove(killed_pid)

    def test_subprocess_exception(self):
        """Tests that exceptions raised in the task are re-raised."""
        workqueue = ndk.workqueue.WorkQueue()

        try:
            workqueue.add_task(raise_error)
            with self.assertRaises(ndk.workqueue.TaskError):
                workqueue.get_result()
        finally:
            workqueue.terminate()
            workqueue.join()


class DummyWorkQueueTest(unittest.TestCase):
    """Tests for DummyWorkQueue."""
    def test_put_func(self):
        """Test that we can pass a function to the queue and get results."""
        workqueue = ndk.workqueue.DummyWorkQueue()

        workqueue.add_task(put, 1)
        workqueue.add_task(put, 2)
        expected_results = [1, 2]

        while expected_results:
            i = workqueue.get_result()
            self.assertIn(i, expected_results)
            expected_results.remove(i)

        workqueue.terminate()
        workqueue.join()

    def test_put_functor(self):
        """Test that we can pass a functor to the queue and get results."""
        workqueue = ndk.workqueue.DummyWorkQueue()

        workqueue.add_task(Functor(1))
        workqueue.add_task(Functor(2))
        expected_results = [1, 2]

        while expected_results:
            i = workqueue.get_result()
            self.assertIn(i, expected_results)
            expected_results.remove(i)

        workqueue.terminate()
        workqueue.join()

    def test_finished(self):
        """Tests that finished() returns the correct result."""
        workqueue = ndk.workqueue.WorkQueue()
        self.assertTrue(workqueue.finished())

        workqueue.add_task(put, 1)
        self.assertFalse(workqueue.finished())
        workqueue.get_result()
        self.assertTrue(workqueue.finished())

        workqueue.terminate()
        workqueue.join()
        self.assertTrue(workqueue.finished())

    def test_subprocess_exception(self):
        """Tests that exceptions raised in the task are re-raised."""
        workqueue = ndk.workqueue.DummyWorkQueue()

        try:
            workqueue.add_task(raise_error)
            with self.assertRaises(ndk.workqueue.TaskError):
                workqueue.get_result()
        finally:
            workqueue.terminate()
            workqueue.join()
