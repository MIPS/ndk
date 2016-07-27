cmake_minimum_required(VERSION 3.6.0)

add_executable(static-executable jni/main.cpp)

# Need -no-pie or -DANDROID_PIE=FALSE,
# because unlike ndk-build,
# these flags are added after the default flags are processed.
set_target_properties(static-executable PROPERTIES LINK_FLAGS "-Wl,-no-pie -static")
