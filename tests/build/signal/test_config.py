def build_unsupported(abi, platform, toolchain):
    if abi in ('arm64-v8a', 'mips64', 'x86_64'):
        return abi
    return None
