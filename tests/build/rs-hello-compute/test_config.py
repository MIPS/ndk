def build_unsupported(abi, platform, toolchain):
    if abi in ('mips', 'mips32r6', 'mips64'):
        return abi
    return None
