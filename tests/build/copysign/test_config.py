def build_broken(abi, platform, toolchain):
    if abi not in ('arm64-v8a', 'mips64', 'x86_64'):
        return abi, 'https://b.android.com/74835'
    return None, None
