def match_unsupported(abi, platform, toolchain, subtest=None):
    if platform < 21:
        return platform
    return None
