def run_unsupported(_abi, device_api, _toolchain, name):
    # Can't replace SIGABRT on old releases.
    if device_api < 21 and name == 'debug_abort.pass':
        return device_api
    return None
