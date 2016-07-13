def match_broken(abi, platform, device_platform, toolchain, subtest=None):
    if platform >= 21:
        return 'android-{}'.format(platform), 'http://b/24468267'
    if (abi == 'x86' and toolchain == 'clang' and
        subtest == 'static-executable'):
        return ' '.join([abi, toolchain]), 'http://b/30101473'
    return None, None
