def build_unsupported(abi, platform, toolchain):
    if abi == 'mips64' or abi == 'mips32r6':
        return abi
    return None

def run_broken(abi, platform, toolchain, name):
    if abi == 'x86_64':
        return abi, 'http://b/38264489'
    return None, None
