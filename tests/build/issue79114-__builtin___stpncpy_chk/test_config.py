def match_unsupported(abi, platform, toolchain, subtest=None):
    platform_version = 0
    if platform is not None:
        platform_version = int(platform.split('-')[1])
    if platform_version < 21:
        return platform
    return None
