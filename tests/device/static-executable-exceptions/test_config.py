def run_broken(abi, _device_api, toolchain, _subtest):
    if abi == 'armeabi-v7a':
        # __gnu_Unwind_Find_exidx has always been broken in libc.a. We need an
        # update to the static libraries to fix this.
        return abi, 'https://github.com/android-ndk/ndk/issues/593'

    return None, None
