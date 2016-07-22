cmake_minimum_required(VERSION 3.6.0)

add_subdirectory(shared)
add_subdirectory(static)
include_directories(shared static)
set(C_LIBRARIES c_shared c_static)
set(CPP_LIBRARIES cpp_shared cpp_static)

if(ANDROID_STL STREQUAL none)
	add_definitions(-DNONE)
elseif(ANDROID_STL STREQUAL system)
	add_definitions(-DSYSTEM)
endif()

add_executable(c_exe exe.c)
target_link_libraries(c_exe ${C_LIBRARIES})

add_executable(cpp_exe exe.cpp)
target_link_libraries(cpp_exe ${C_LIBRARIES} ${CPP_LIBRARIES})
