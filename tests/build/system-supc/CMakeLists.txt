cmake_minimum_required(VERSION 3.6.0)

add_library(foo SHARED jni/foo.cpp)
set_property(TARGET foo PROPERTY CXX_STANDARD 11)
