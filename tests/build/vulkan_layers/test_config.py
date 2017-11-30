def build_unsupported(abi, platform, toolchain):
    # Vulkan isn't supported on armeabi
    if abi == 'armeabi':
        return abi

    # Vulkan support wasn't added until android-24
    if platform < 24:
        return platform

    # Not supported with GCC.
    if toolchain == '4.9':
        return toolchain

    return None
