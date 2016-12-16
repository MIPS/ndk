def run_broken(abi, device_api, toolchain, subtest):
    # These were marked broken when we inherited them, so there's only one bug
    # for the whole group.
    legacy_broken = (
        'elide2',
        'new3',
        'terminate1',
        'weak1',
    )
    if subtest in legacy_broken:
        return toolchain, 'http://b/24541258'

    if subtest == 'badalloc1' and device_api == 23:
        return device_api, 'http://b/26002885'

    if subtest == 'filter1' and device_api >= 21 and toolchain == '4.9':
        return '{} {}'.format(device_api, toolchain), 'http://b/24403847'

    return None, None
