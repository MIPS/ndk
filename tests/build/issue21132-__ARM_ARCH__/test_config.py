def match_unsupported(abi, platform, toolchain, subtest=None):
    if abi not in ('armeabi-v7a', 'x86'):
        return abi
    return None
