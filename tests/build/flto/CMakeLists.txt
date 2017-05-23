cmake_minimum_required(VERSION 3.6.0)

SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -flto")
SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -flto")

if(NOT MIPS AND NOT MIPS64)
  SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fuse-ld=gold")
endif()

add_library(bar STATIC jni/bar.c)

add_executable(flto jni/flto.c)
target_link_libraries(flto bar)
