def run_broken(abi, _device_api, _toolchain, name):
    if abi == 'arm64-v8a' and name == 'do_allocate_and_deallocate.pass':
        return abi, 'https://github.com/android-ndk/ndk/issues/375'
    return None, None
