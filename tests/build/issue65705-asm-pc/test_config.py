def build_broken(abi, device, toolchain):
    if toolchain == '4.9':
        return toolchain, 'http://b.android.com/65705'
    return None, None


def build_unsupported(abi, device, toolchain):
    if abi not in ('armeabi', 'armeabi-v7a'):
        return abi
    return None
