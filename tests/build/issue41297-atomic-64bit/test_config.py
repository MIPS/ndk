def match_unsupported(abi, platform, toolchain, subtest=None):
    if abi == 'mips' or abi == 'mips32r6':
        return abi, 'http://b.android.com/41297'
    return None
