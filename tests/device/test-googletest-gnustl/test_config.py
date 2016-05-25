def match_unsupported(abi, platform, device_platform, toolchain, subtest=None):
    if (abi == 'x86' and platform < 17) or (abi == 'mips' and platform < 12):
        return abi
    return None
