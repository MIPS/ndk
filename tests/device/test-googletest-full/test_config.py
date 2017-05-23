def run_broken(abi, _device_api, toolchain, name):
    if abi == 'armeabi' and toolchain == 'clang' and name == 'gtest_all_test':
        return abi, 'https://github.com/android-ndk/ndk/issues/374'

    if abi in ('x86', 'x86_64'):
        return abi, 'http://b/24380035'

    return None, None
