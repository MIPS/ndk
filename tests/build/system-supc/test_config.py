def extra_cmake_flags():
    return ['-DANDROID_STL=system', '-DANDROID_CPP_FEATURES=exceptions']
