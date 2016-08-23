def run_broken(abi, device_api, toolchain, subtest):
    if device_api <= 10 and subtest == 'issue19851-sigsetjmp':
        return device_api, 'http://b/26015756'
    return None, None


def build_unsupported(abi, platform, toolchain):
    if abi in ('x86', 'mips') and platform < 12:
        return abi
    return None
