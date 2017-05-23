cmake_minimum_required(VERSION 3.6.0)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fopenmp")
set(CMAKE_EXECUTABLE_LINKER_FLAGS "${CMAKE_EXECUTABLE_LINKER_FLAGS} -fopenmp")

add_executable(openmp jni/openmp.c)
add_executable(openmp2 jni/openmp2.c)
add_executable(fib jni/fib.c)
