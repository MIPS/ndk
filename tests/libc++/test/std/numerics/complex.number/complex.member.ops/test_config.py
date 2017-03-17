def build_broken(abi, api, toolchain, name):
    broken_abis = ('arm64-v8a', 'x86_64')
    if abi in broken_abis and name == 'divide_equal_complex.pass':
        return abi, 'https://github.com/android-ndk/ndk/issues/294'
    return None, None
