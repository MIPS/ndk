def build_unsupported(abi, platform, toolchain):
    if toolchain != '4.9':
        return toolchain
    return None
