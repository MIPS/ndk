def build_broken(abi, platform, toolchain):
    if toolchain == 'clang' and abi.startswith('mips'):
        return toolchain, 'http://b/25937032'
    return None, None
