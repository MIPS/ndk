def build_unsupported(abi, platform, toolchain):
    if abi != 'armeabi-v7a':
        return abi
    if toolchain != '4.9':
        return toolchain
    return None
