def run_broken(abi, device_api, toolchain, name):
    lp64_abis = ('arm64-v8a', 'mips64', 'x86_64')
    if abi in lp64_abis and name == 'put_long_double.pass':
        return abi, 'http://b/34950416'
    percent_f_tests = ('put_double.pass', 'put_long_double.pass')
    if name in percent_f_tests and device_api < 21:
        return 'android-{}'.format(device_api), 'http://b/35764716'
    if name == 'put_long_double.pass':
        return 'all?', 'http://b/63144639'
    return None, None
