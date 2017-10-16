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
"""Python interfaces for win32 APIs."""
from __future__ import absolute_import

import ctypes
import ctypes.wintypes


# From winnt.h
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectExtendedLimitInformation = 9


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('ReadOperationCount', ctypes.c_ulonglong),
        ('WriteOperationCount', ctypes.c_ulonglong),
        ('OtherOperationCount', ctypes.c_ulonglong),
        ('ReadTransferCount', ctypes.c_ulonglong),
        ('WriteTransferCount', ctypes.c_ulonglong),
        ('OtherTransferCount', ctypes.c_ulonglong),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('PerProcessUserTimeLimit', ctypes.wintypes.LARGE_INTEGER),
        ('PerJobUserTimeLimit', ctypes.wintypes.LARGE_INTEGER),
        ('LimitFlags', ctypes.wintypes.DWORD),
        ('MinimumWorkingSetSize', ctypes.c_size_t),
        ('MaximumWorkingSetSize', ctypes.c_size_t),
        ('ActiveProcessLimit', ctypes.wintypes.DWORD),
        ('Affinity', ctypes.POINTER(ctypes.c_ulong)),
        ('PriorityClass', ctypes.wintypes.DWORD),
        ('SchedulingClass', ctypes.wintypes.DWORD),
    ]

class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ('IoInfo', IO_COUNTERS),
        ('ProcessMemoryLimit', ctypes.c_size_t),
        ('JobMemoryLimit', ctypes.c_size_t),
        ('PeakProcessMemoryUsed', ctypes.c_size_t),
        ('PeakJobMemoryUsed', ctypes.c_size_t),
    ]


def CreateJobObject(attributes=None, name=None):
    job = ctypes.windll.kernel32.CreateJobObjectA(attributes, name)
    if job is None:
        # Automatically calls GetLastError and FormatError for us to create the
        # WindowsError exception.
        raise ctypes.WinError()
    return job


def SetInformationJobObject(job, info_class, info):
    result = ctypes.windll.kernel32.SetInformationJobObject(
        job, JobObjectExtendedLimitInformation,
        ctypes.pointer(info), ctypes.sizeof(info))
    if not result:
        raise ctypes.WinError()


def AssignProcessToJobObject(job, process):
    if not ctypes.windll.kernel32.AssignProcessToJobObject(job, process):
        raise ctypes.WinError()


def GetCurrentProcess():
    return ctypes.windll.kernel32.GetCurrentProcess()


def CloseHandle(handle):
    if not ctypes.windll.kernel32.CloseHandle(handle):
        raise ctypes.WinError()
