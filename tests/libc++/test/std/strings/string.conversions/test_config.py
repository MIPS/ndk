def run_broken(abi, device_api, toolchain, name):
    lp64_abis = ('arm64-v8a', 'mips64', 'x86_64')
    if device_api < 26 and abi in lp64_abis and name == 'stold.pass':
        return 'android-{}'.format(device_api), 'http://b/31101647'
    if abi not in lp64_abis and name == 'stof.pass':
        return 'all', 'http://b/34739876'
    return None, None
