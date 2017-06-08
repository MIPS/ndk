def run_broken(abi, device_api, toolchain, name):
    lp64_abis = ('arm64-v8a', 'mips64', 'x86_64')
    failing_tests = (
        'get_long_double.pass',
    )
    if abi in lp64_abis and device_api < 26 and name in failing_tests:
        return 'android-{}'.format(device_api), 'http://b/31101647'

    if abi not in lp64_abis and name == 'get_float.pass':
        return abi, 'https://github.com/android-ndk/ndk/issues/415'

    return None, None
