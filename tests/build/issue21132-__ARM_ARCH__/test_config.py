def build_unsupported(abi, platform, toolchain):
    if abi not in ('armeabi-v7a', 'x86'):
        return abi
    return None
