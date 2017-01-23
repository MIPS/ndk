"""Tests that libandroid_support is linked when using libc++_shared in cmake.

We use libc++_shared and use a function that is only defined in
libandroid_support. If we're not linking it, we'll fail to build.
"""


def extra_cmake_flags():  # pylint: disable=missing-docstring
    return ['-DANDROID_STL=c++_shared']
