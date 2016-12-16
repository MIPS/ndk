def build_unsupported(abi, platform, toolchain):
    if not toolchain.startswith('clang'):
        return toolchain
    if not abi.startswith('armeabi') and not abi == 'x86':
        return abi
    return None


def run_unsupported(abi, device_api, toolchain, subtest):
    if device_api < 19:
        return device_api
    return None


def run_broken(abi, device_api, toolchain, subtest):
    if abi == 'x86':
        return abi, 'http://b.android.com/230369'
    return None, None
