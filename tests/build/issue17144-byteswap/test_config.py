def build_broken(abi, platform, toolchain):
    if toolchain == 'clang' and abi.startswith('armeabi-v7a'):
        return '{} {}'.format(toolchain, abi), 'http://b/26091410'
    if toolchain == 'clang' and abi == 'mips':
        return '{} {}'.format(toolchain, abi), 'https://github.com/android-ndk/ndk/issues/159'
    return None, None
