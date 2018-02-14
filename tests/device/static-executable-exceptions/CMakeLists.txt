cmake_minimum_required(VERSION 3.6.0)

add_executable(static-executable jni/main.cpp)

set_target_properties(
  static-executable PROPERTIES LINK_FLAGS "-static -Wl,--eh-frame-hdr")
