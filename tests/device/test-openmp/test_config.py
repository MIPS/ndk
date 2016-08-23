def build_broken(abi, platform, toolchain):
    if toolchain == 'clang':
        return toolchain, 'http://b/25937032'
    return None, None
