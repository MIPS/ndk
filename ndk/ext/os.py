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
"""Helpers for os APIs."""
from __future__ import absolute_import

import contextlib
import os


@contextlib.contextmanager
def replace_environ(env):
    """Replacing os.environ with env, restoring on context exit.

    The values in env replace the existing environment rather than adding to or
    modifying it. To modify the existing environment, use modify_environ.

    Args:
        env: Environment dict to use as the new environment.
    """
    old_environ = dict(os.environ)
    try:
        os.environ = env
        yield
    finally:
        os.environ = old_environ


def modify_environ(env):
    """Extends os.environ with the values in env, restoring on context exit.

    The values in env add to the existign environment rather than completely
    replacing the existing environment. To replace the environment entirely,
    use replace_environ.

    Args:
        env: Environment dict to be merged with the existing environment.
    """
    new_environ = dict(os.environ)
    for key, value in env.items():
        new_environ[key] = value
    return replace_environ(new_environ)
