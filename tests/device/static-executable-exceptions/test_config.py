def match_broken(abi, platform, device_platform, toolchain, subtest=None):
    if platform >= 21:
        return 'android-{}'.format(platform), 'http://b/24468267'
    return None, None
