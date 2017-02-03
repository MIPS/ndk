def build_broken(abi, api, toolchain, name):
    if abi == 'arm64-v8a' and name in ('atan.pass', 'atanh.pass'):
        return abi, 'https://github.com/android-ndk/ndk/issues/294'
    return None, None
