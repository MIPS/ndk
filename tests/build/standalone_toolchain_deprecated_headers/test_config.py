# Shut up a warning about us not being a real package.
from __future__ import absolute_import


def build_broken(_abi, _api_level, toolchain):
    if toolchain == '4.9':
        # GCC's default include ordering is wrong, preventing the C++ stdlib
        # from overriding compiler headers. In this case we can't include
        # <cstddef> because the include_next can't find the compiler's header.
        return toolchain, 'http://b/30096326'
    return None, None
