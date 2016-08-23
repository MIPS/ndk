def build_unsupported(abi, platform, toolchain):
    if abi in ('x86', 'mips') and platform < 12:
        return abi
    return None
