cmake_minimum_required(VERSION 3.6.0)

enable_language(ASM_NASM)

add_executable(test-yasm jni/test-yasm.c jni/print_hello.asm)
