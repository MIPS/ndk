cmake_minimum_required(VERSION 3.6.0)

add_library(c_shared SHARED shared.c)

if(NOT ANDROID_STL MATCHES "^(none|system)$")
	add_library(cpp_shared SHARED shared.cpp)
endif()
