def build_unsupported(abi, platform, toolchain):
    if abi in ('mips', 'mips64'):
        return abi
    return None
