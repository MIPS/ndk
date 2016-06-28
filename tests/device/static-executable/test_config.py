def match_broken(abi, platform, device_platform, toolchain, subtest=None):
    bug = 'https://github.com/android-ndk/ndk/issues/132'
    if platform >= 21:
        return 'android-{}'.format(platform), bug
    return None, None
