cmake_minimum_required(VERSION 3.6.0)

add_executable(test_basic_exceptions jni/test_basic_exceptions.cpp)
set_target_properties(test_basic_exceptions PROPERTIES
  COMPILE_FLAGS -fexceptions)
