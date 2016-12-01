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
"""Helper functions for NDK build and test paths."""
import os

import build.lib.build_support as build_support
import config


def get_install_path(out_dir=None):
    """Returns the built NDK install path.

    Note that the path returned might not actually contain the NDK. The NDK may
    not actually be present if:

    * The NDK hasn't been built yet.
    * The name of the release has changed since the NDK was built.
    * out_dir is not consistent with the build.

    Args:
        out_dir: Optional base out directory. Inferred from $OUT_DIR if not
                 supplied.

    Returns:
        Directory that the built NDK should be installed to.
    """
    if out_dir is None:
        out_dir = build_support.get_out_dir()
    release_name = 'android-ndk-{}'.format(config.release)
    return os.path.join(out_dir, release_name)
