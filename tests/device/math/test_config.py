def build_unsupported(abi, platform, toolchain):
    if platform < 18:
        return platform
    return None


def run_unsupported(abi, device_api, toolchain, subtest):
    if device_api < 18:
        return device_api
    return None
