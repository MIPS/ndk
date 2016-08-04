def match_unsupported(abi, platform, device_platform, toolchain, subtest=None):
    # Vulkan isn't supported on armeabi
    if abi == 'armeabi':
        return abi

    # Vulkan support wasn't added until android-24
    if device_platform < 24 and subtest != None:
        return device_platform

    return None
