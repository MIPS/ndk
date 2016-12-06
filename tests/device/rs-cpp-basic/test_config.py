def build_unsupported(abi, platform, toolchain):
    if abi == 'mips64':
        return abi
    return None
