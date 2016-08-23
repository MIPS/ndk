def run_broken(abi, device_platform, toolchain, subtest):
    if subtest == 'test_1_static' and abi == 'mips':
        return abi, 'http://b/24673473'
    return None, None
