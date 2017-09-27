def run_broken(abi, _device_api, toolchain, name):
    if abi in ('x86', 'x86_64'):
        return abi, 'http://b/24380035'

    return None, None
