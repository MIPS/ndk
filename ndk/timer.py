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
import datetime
import timeit


class Timer(object):
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None

    def start(self):
        self.start_time = timeit.default_timer()

    def finish(self):
        self.end_time = timeit.default_timer()

        # Not interested in partial seconds at this scale.
        seconds = int(self.end_time - self.start_time)
        self.duration = datetime.timedelta(seconds=seconds)

    def __enter__(self):
        self.start()

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.finish()
