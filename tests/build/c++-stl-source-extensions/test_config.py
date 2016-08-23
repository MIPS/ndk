# Shut up a warning about us not being a real package.
from __future__ import absolute_import
import platform


def build_unsupported(_abi, _api_level, _toolchain):
    if platform.system() == 'Windows':
        # This test is specifically checking that we can handle all the
        # different C++ source extensions, including those that differ only by
        # case. Windows is case insensitive, so this test fails hard.
        return platform.system()
    return None
