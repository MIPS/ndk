def match_unsupported(abi, platform, toolchain, subtest=None):
    if abi != 'armeabi-v7a':
        return abi
    return None


def extra_cmake_flags():
    return ['-DANDROID_ARM_NEON=TRUE']
