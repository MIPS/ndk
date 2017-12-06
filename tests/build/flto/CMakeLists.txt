cmake_minimum_required(VERSION 3.6.0)

SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -flto")
SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -flto")

add_library(bar STATIC jni/bar.c)

add_executable(flto jni/flto.c)
target_link_libraries(flto bar)
