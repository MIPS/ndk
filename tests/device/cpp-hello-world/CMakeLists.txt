cmake_minimum_required(VERSION 3.6.0)

if(ANDROID_STL STREQUAL none)
	add_definitions(-DNONE)
elseif(ANDROID_STL STREQUAL system)
	add_definitions(-DSYSTEM)
endif()

add_executable(hello-world jni/hello-world.cpp)
