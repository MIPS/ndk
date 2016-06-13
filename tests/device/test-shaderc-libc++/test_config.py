def match_unsupported(abi, platform, device_platform, toolchain, subtest=None):
    if abi == 'armeabi':
        return abi
    return None


def match_broken(abi, platform, device_platform, toolchain, subtest=None):
    return 'all', 'http://b/29216817'
