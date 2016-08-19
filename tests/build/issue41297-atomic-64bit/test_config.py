def build_unsupported(abi, platform, toolchain):
    if abi == 'mips':
        return abi, 'http://b.android.com/41297'
    return None
