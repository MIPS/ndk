# Shut up a warning about us not being a real package.
from __future__ import absolute_import


def build_unsupported(abi, _api_level, _toolchain):
    # -mthumb is only relevant for 32-bit ARM.
    if abi not in ('armeabi', 'armeabi-v7a'):
        return abi
    return None
