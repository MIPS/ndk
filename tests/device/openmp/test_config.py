def build_broken(abi, platform, toolchain):
    if toolchain == 'clang' and abi == 'mips':
        # mips doesn't have __sync_fetch_and_add_8 in libatomic.
        return toolchain, 'http://b/25937032'
    return None, None
