def run_broken(abi, device_api, toolchain, name):
    lp64_abis = ('arm64-v8a', 'mips64', 'x86_64')
    if abi in lp64_abis and name == 'put_long_double.pass':
        return abi, 'http://b/34950416'
    if name == 'put_double.pass' and device_api < 21:
        return 'android-{}'.format(device_api), 'http://b/35764716'
    return None, None
