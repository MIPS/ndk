//
// Copyright (C) 2016 The Android Open Source Project
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

// The best case for this test would be that we readelf to get all the symbols
// present in each version and make sure they can be referred to in every
// following version. We don't have a good way to actually write that test
// though.

#include <signal.h>

// This isn't exposed in the newer headers.
extern "C" sighandler_t bsd_signal(int, sighandler_t);

void foo() {
    // signal(2) was an inline (!) referring to bsd_signal until android-21. If
    // we use it in a static library built against android-9 and then link that
    // into one built against android-21, we'd get a link error unless
    // android-21 also provides bsd_signal. We build this against android-21, so
    // make sure we can resolve a call to bsd_signal.
    // https://github.com/android-ndk/ndk/issues/160
    bsd_signal(SIGINT, NULL);
}
