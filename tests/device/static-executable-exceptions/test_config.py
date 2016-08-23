def build_broken(abi, platform, toolchain):
    if platform >= 21:
        return 'android-{}'.format(platform), 'http://b/24468267'
    return None, None


def run_broken(abi, device_api, toolchain, subtest=None):
    if (abi == 'x86' and toolchain == 'clang' and
        subtest == 'static-executable'):
        return ' '.join([abi, toolchain]), 'http://b/30101473'
    return None, None
