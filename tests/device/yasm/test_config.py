def build_unsupported(abi, platform, toolchain):
    if abi not in ('x86', 'x86_64'):
        return abi
    return None

def build_broken(abi, platform, toolchain):
    if abi == 'x86_64':
        return abi, 'http://b/24620865'
    return None, None
