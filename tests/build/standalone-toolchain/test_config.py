# Shut up a warning about us not being a real package.
from __future__ import absolute_import
import platform


def match_broken(abi, api_level, toolchain):
    if toolchain == '4.9':
        # GCC's default include ordering is wrong, preventing the C++ stdlib
        # from overriding compiler headers. In this case we can't include
        # <cstddef> because the include_next can't find the compiler's header.
        return toolchain, 'http://b/30096326'
    return None, None


def match_unsupported(_abi, _api_level, _toolchain, _subtest=None):
    if platform.system() == 'Windows':
        # make-standalone-toolchain.sh isn't supported on Windows since we
        # don't have bash. Note that platform.system() won't report "Windows"
        # for cygwin, so we will run the test in that case.
        return platform.system()
    return None
