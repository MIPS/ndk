def run_broken(abi, device_api, toolchain, subtest):
    lp64_abis = ('arm64-v8a', 'mips64', 'x86_64')
    if subtest == 'test_stlport' and abi in lp64_abis:
        return abi, 'http://b/24614189'
    return None, None
