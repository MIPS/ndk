def run_broken(abi, device_api, toolchain, subtest):
    if subtest == 'test_wait-static' and abi == 'x86':
        return abi, 'http://b/24507500'
    return None, None
