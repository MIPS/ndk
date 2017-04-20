def run_broken(abi, device_api, toolchain, name):
    if name == 'F.pass' and device_api < 18:
        return 'android-{}'.format(device_api), 'http://b/2643900'
    return None, None
