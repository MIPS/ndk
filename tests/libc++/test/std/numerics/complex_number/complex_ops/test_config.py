def build_broken(abi, api, toolchain, name):
    broken_tests = (
        'complex_divide_complex.pass',
        'scalar_divide_complex.pass',
    )
    if abi == 'arm64-v8a' and name in broken_tests:
        return abi, 'https://github.com/android-ndk/ndk/issues/294'
    return None, None
