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


class UseLastErrorWinDLL(ctypes.WinDLL):
    def __init__(self, name, mode=ctypes.DEFAULT_MODE, handle=None):
        super(UseLastErrorWinDLL, self).__init__(name, mode, handle, use_last_error=True)

_LOADER = ctypes.LibraryLoader(UseLastErrorWinDLL)


def CreateJobObject(attributes=None, name=None):
    fn_CreateJobObjectW = _LOADER.kernel32.CreateJobObjectW
    fn_CreateJobObjectW.restype = ctypes.wintypes.HANDLE
    fn_CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    job = fn_CreateJobObjectW(attributes, name)
    if job is None:
        # Automatically calls GetLastError and FormatError for us to create the
        # WindowsError exception.
        raise ctypes.WinError(ctypes.get_last_error())
    return job


def SetInformationJobObject(job, info_class, info):
    fn_SetInformationJobObject = _LOADER.kernel32.SetInformationJobObject
    fn_SetInformationJobObject.restype = ctypes.wintypes.BOOL
    fn_SetInformationJobObject.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.wintypes.DWORD
    ]
    result = fn_SetInformationJobObject(
        job, JobObjectExtendedLimitInformation,
        ctypes.pointer(info), ctypes.sizeof(info))
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())


def AssignProcessToJobObject(job, process):
    fn_AssignProcessToJobObject = _LOADER.kernel32.AssignProcessToJobObject
    fn_AssignProcessToJobObject.restype = ctypes.wintypes.BOOL
    fn_AssignProcessToJobObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.HANDLE]
    if not fn_AssignProcessToJobObject(job, process):
        raise ctypes.WinError(ctypes.get_last_error())


def GetCurrentProcess():
    fn_GetCurrentProcess = _LOADER.kernel32.GetCurrentProcess
    fn_GetCurrentProcess.restype = ctypes.wintypes.HANDLE
    return fn_GetCurrentProcess()


def CloseHandle(handle):
    fn_CloseHandle = _LOADER.kernel32.CloseHandle
    fn_CloseHandle.restype = ctypes.wintypes.BOOL
    fn_CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
    if not fn_CloseHandle(handle):
        raise ctypes.WinError(ctypes.get_last_error())
