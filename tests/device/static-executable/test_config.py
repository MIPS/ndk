def extra_cmake_flags():
    # Need -DANDROID_PIE=FALSE, because unlike ndk-build, these flags are added
    # after the default flags are processed.
    return ['-DANDROID_PIE=FALSE']
