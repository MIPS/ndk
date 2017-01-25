def build_broken(abi, api, toolchain, name):
    if name == 'quick_exit.pass' and api < 21:
        return 'android-{}'.format(api), 'http://b/34719339'
    return None, None
