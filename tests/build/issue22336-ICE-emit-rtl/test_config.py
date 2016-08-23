def build_unsupported(abi, platform, toolchain):
    if abi != 'armeabi-v7a':
        return abi
    return None
