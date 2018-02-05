def build_unsupported(abi, platform, toolchain):
    if abi in ('mips', 'mips32r6'):
        return abi, 'http://b.android.com/41297'
    return None
