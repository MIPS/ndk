cmake_minimum_required(VERSION 3.6.0)

enable_language(ASM)
add_library(neon-asm STATIC jni/foo.S)
