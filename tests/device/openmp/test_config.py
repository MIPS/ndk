def build_broken(abi, platform, toolchain):
    if toolchain == 'clang' and (abi == 'mips' or abi == 'mips32r6'):
        # mips doesn't have __sync_fetch_and_add_8 in libatomic.
        return '{} {}'.format(toolchain, abi), 'http://b/25937032'
    return None, None
