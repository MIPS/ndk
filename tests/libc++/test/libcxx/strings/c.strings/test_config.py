def build_broken(abi, device_api, toolchain, name):
    if name == 'version_cuchar.pass':
        return 'all', 'http://b/63679176'
    return None, None
