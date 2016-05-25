def match_unsupported(abi, platform, device_platform, toolchain, subtest=None):
    if abi in ('x86', 'mips') and platform < 12:
        return abi
    return None
