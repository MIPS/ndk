def run_broken(abi, device_api, toolchain, name):
    if name == 'stof.pass':
        return 'all', 'http://b/34739876'
    return None, None
