def run_broken(abi, device_api, toolchain, subtest):
    if abi.startswith('armeabi') and device_api <= 10 and subtest == 'foo':
        return '{} {}'.format(abi, device_api), 'http://b/28044141'
    return None, None
