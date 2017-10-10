section .rodata
  fmt db "Hello, %s!", 10, 0

section .text
  global print_hello:function
  extern printf

  print_hello:
    mov  rsi, rdi
    lea  rdi, [rel fmt]
    jmp printf wrt ..plt
