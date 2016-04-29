def match_unsupported(abi, platform, device_platform, toolchain, subtest=None):
    if abi != 'armeabi-v7a':
        return abi
    return None
