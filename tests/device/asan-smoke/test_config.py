def build_unsupported(abi, platform, toolchain):
    if not toolchain.startswith('clang'):
        return toolchain
    if not abi.startswith('armeabi') and not abi == 'x86':
        return abi
    return None


def run_unsupported(abi, device_api, _toolchain, subtest):
    if device_api < 19:
        return device_api
    return None


def run_broken(abi, _device_api, _toolchain, _subtest):
    if abi == 'x86_64':
        return abi, 'http://b/72816091'
    return None, None
