def build_unsupported(abi, platform, toolchain):
    if platform < 21:
        return platform
    return None
