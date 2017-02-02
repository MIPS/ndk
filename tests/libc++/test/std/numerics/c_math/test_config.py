def build_broken(abi, api, toolchain, name):
    if name == 'cmath_isnan.pass':
        return 'all', 'http://b/34724220'
    if name == 'cmath_isinf.pass' and api >= 21:
        return 'android-{}'.format(api), 'http://b/34724220'
    return None, None
