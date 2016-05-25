def match_broken(abi, platform, device_platform, toolchain, subtest=None):
    if device_platform <= 10 and subtest == 'issue19851-sigsetjmp':
        return device_platform, 'http://b/26015756'
    return None, None


def match_unsupported(abi, platform, device_platform, toolchain, subtest=None):
    if abi in ('x86', 'mips') and platform < 12:
        return abi
    return None
