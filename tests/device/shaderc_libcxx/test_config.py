def build_unsupported(abi, platform, toolchain):
    if abi == 'armeabi':
        return abi

    # The shaderc makefiles set -Werror -Wattributes, and GCC is not compatible
    # with the definition of abs in libc++'s math.h.
    #
    # Marking as unsupported rather than broken since GCC is deprecated so this
    # isn't a bug (it still works fine if the user isn't using
    # -Werror=attributes).
    if toolchain == '4.9':
        return toolchain

    return None
