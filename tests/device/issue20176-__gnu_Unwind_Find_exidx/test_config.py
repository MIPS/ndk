def build_unsupported(abi, platform, toolchain):
    if abi not in ('armeabi', 'armeabi-v7a'):
        return abi
    return None
