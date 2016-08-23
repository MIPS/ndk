def build_unsupported(abi, platform, toolchain):
    if abi != 'x86':
        return abi

    # mm_malloc.h depends on posix_memalign, which wasn't added until
    # android-16.
    if platform < 16:
        return platform

    return None
