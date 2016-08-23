def build_broken(abi, platform, toolchain):
    if abi == 'x86':
        return abi, 'http://b/25981507'
    return None, None


def build_unsupported(abi, platform, toolchain):
    if not toolchain.startswith('clang'):
        return toolchain
    if not abi.startswith('armeabi') and not abi == 'x86':
        return abi
    if platform < 19:
        return platform
    return None
