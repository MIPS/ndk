cmake_minimum_required(VERSION 3.6.0)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
add_executable(foo foo.cpp)
