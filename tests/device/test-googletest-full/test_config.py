def match_unsupported(abi, platform, device_platform, toolchain, subtest=None):
    platform_version = 0
    if platform is not None:
        platform_version = int(platform.split('-')[1])
    if (abi == 'x86' and platform_version < 17) or (abi == 'mips' and platform_version < 12):
        return abi
    return None
