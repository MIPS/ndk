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
"""Tests for ndk.ext.os."""
from __future__ import absolute_import

import os
import unittest

import ndk.ext.os


class OsTest(unittest.TestCase):
    def test_replace_environ(self):
        self.assertIn('PATH', os.environ)
        old_path = os.environ['PATH']
        self.assertNotIn('FOO', os.environ)

        with ndk.ext.os.replace_environ({'FOO': 'bar'}):
            self.assertNotIn('PATH', os.environ)
            self.assertIn('FOO', os.environ)
            self.assertEqual(os.environ['FOO'], 'bar')

        self.assertIn('PATH', os.environ)
        self.assertEqual(os.environ['PATH'], old_path)
        self.assertNotIn('FOO', os.environ)

    def test_modify_environ(self):
        self.assertIn('PATH', os.environ)
        old_path = os.environ['PATH']
        self.assertNotIn('FOO', os.environ)

        with ndk.ext.os.modify_environ({'FOO': 'bar'}):
            self.assertIn('PATH', os.environ)
            self.assertEqual(os.environ['PATH'], old_path)
            self.assertIn('FOO', os.environ)
            self.assertEqual(os.environ['FOO'], 'bar')

        self.assertIn('PATH', os.environ)
        self.assertEqual(os.environ['PATH'], old_path)
        self.assertNotIn('FOO', os.environ)
