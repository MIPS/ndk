cmake_minimum_required(VERSION 3.6.0)

add_library(c_static STATIC static.c)

if(NOT ANDROID_STL MATCHES "^(none|system)$")
	add_library(cpp_static STATIC static.cpp)
endif()
