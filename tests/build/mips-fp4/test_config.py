def build_unsupported(abi, platform, toolchain):
    if abi != 'mips':
        return abi
    return None


def build_broken(abi, platform, toolchain):
    if toolchain == 'clang':
        return toolchain, 'http://b/26984979'
    return None, None
