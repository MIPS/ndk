def extra_cmake_flags():
    # Clang does the right thing if you provide `-pie -static`, but GCC throws
    # an error.
    return ['-DANDROID_PIE=OFF']


def build_unsupported(_abi, api, _toolchain):
    # Static executables with libc++ require targeting a new enough API level
    # to not need libandroid_support.
    if api < 21:
        return 'android-{}'.format(api)

    return None
