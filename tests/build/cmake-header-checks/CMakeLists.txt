cmake_minimum_required(VERSION 3.6.0)

include (CheckIncludeFile)

CHECK_INCLUDE_FILE(pthread.h HAVE_PTHREAD)

if (NOT HAVE_PTHREAD)
  message(FATAL_ERROR "Could not find pthread.h")
endif()

add_executable(foo foo.cpp)
