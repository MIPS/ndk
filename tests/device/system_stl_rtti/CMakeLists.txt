cmake_minimum_required(VERSION 3.6.0)

add_executable(test_basic_rtti jni/test_basic_rtti.cpp)
set_target_properties(test_basic_rtti PROPERTIES
  COMPILE_FLAGS -frtti)
