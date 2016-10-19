def build_unsupported(abi, platform, toolchain):
    # Vulkan isn't supported on armeabi
    if abi == 'armeabi':
        return abi

    # Vulkan support wasn't added until android-24
    if platform < 24:
        return platform

    return None


def build_broken(abi, platform, toolchain):
    if toolchain == '4.9':
        return toolchain, 'http://b/31021045'
    elif toolchain == 'clang' and abi == 'armeabi-v7a':
        return toolchain, 'http://b/32255384'
    return None, None
