def run_broken(_abi, api, _toolchain, name):
    if api < 21 and name == 'io.pass':
        bug = 'https://issuetracker.google.com/36988114'
        return 'android-{}'.format(api), bug
    return None, None