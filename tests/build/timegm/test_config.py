def build_unsupported(_abi, api, _toolchain):
    if api < 12:
        return api
    return None
