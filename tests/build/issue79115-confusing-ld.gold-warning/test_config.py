def build_broken(abi, _api, toolchain):
    if abi.startswith('mips') and toolchain == 'clang':
        bug = 'https://github.com/android-ndk/ndk/issues/376'
        return '{} {}'.format(abi, toolchain), bug
    return None, None
