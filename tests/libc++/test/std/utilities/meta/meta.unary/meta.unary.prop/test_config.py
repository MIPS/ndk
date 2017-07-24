def build_broken(_abi, _api, toolchain, name):
    if toolchain == 'clang' and name == 'is_trivially_copyable.pass':
        return toolchain, 'http://b/63936549'
    return None, None
