def match_unsupported(abi, platform, toolchain, subtest=None):
    if abi != 'armeabi-v7a':
        return abi
    if toolchain != '4.9':
        return toolchain
    return None
