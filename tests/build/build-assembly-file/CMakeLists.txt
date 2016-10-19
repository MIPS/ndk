cmake_minimum_required(VERSION 3.6)

enable_language(ASM)

if(CMAKE_SYSTEM_PROCESSOR STREQUAL armv7-a)
  set(TEST_SOURCES jni/assembly1.s jni/assembly2.S)
elseif(CMAKE_SYSTEM_PROCESSOR STREQUAL i686)
  set(TEST_SOURCES jni/assembly-x86.S)
elseif(CMAKE_SYSTEM_PROCESSOR STREQUAL mips)
  set(TEST_SOURCES jni/assembly-mips.S)
endif()

add_library(test_build_assembly SHARED ${TEST_SOURCES})
# Without C or C++ files, CMake doesn't know which linker to use.
set_target_properties(test_build_assembly PROPERTIES LINKER_LANGUAGE C)
