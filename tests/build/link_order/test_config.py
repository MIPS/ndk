def build_unsupported(_abi, _api, toolchain):
    if toolchain != 'clang':
        return toolchain
    return None
