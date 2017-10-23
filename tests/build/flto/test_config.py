# Shut up a warning about us not being a real package.
from __future__ import absolute_import
import platform


def build_unsupported(abi, _platform, toolchain):
    # Clang does LTO via gold plugin, but gold doesn't support MIPS yet.
    if toolchain == 'clang' and abi.startswith('mips'):
        return '{} {}'.format(toolchain, abi)

    return None


def build_broken(_abi, _platform, toolchain):
    # We don't support LTO on Windows.
    if platform.system() == 'Windows' and toolchain == 'clang':
        bug = 'https://github.com/android-ndk/ndk/issues/251'
        return '{} {}'.format(platform.system(), toolchain), bug

    return None, None
