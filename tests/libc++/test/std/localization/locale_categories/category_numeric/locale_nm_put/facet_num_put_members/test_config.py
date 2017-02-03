def run_broken(abi, device_api, toolchain, name):
    lp64_abis = ('arm64-v8a', 'mips64', 'x86_64')
    if abi in lp64_abis and name == 'put_long_double.pass':
        return abi, 'http://b/34950416'
    return None, None
