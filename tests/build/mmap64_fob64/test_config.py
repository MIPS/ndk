def build_unsupported(_abi, api, toolchain):
    if toolchain == '4.9' and api < 21:
        return 'gcc android-{}'.format(api)
    return None
