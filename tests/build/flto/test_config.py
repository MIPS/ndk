# Shut up a warning about us not being a real package.
from __future__ import absolute_import
import platform


def build_unsupported(abi, _platform, toolchain):
    # Clang does LTO via gold plugin, but gold doesn't support MIPS yet.
    if toolchain == 'clang' and abi.startswith('mips'):
        return '{} {}'.format(toolchain, abi)

    return None
