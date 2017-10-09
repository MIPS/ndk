section .rodata
  fmt db "Hello, %s!", 10, 0

section .text
  global print_hello:function
  extern printf
  extern _GLOBAL_OFFSET_TABLE_

  print_hello:
    sub  esp, 28
    mov  [esp+8], ebx
    call .init_got
    .init_got:
    pop  ebx
    add  ebx, _GLOBAL_OFFSET_TABLE_+$$-.init_got wrt ..gotpc
    lea  eax, [ebx+fmt wrt ..gotoff]
    mov  [esp], eax
    mov  eax, [esp+32]
    mov  [esp+4], eax
    call printf wrt ..plt
    mov  ebx, [esp+8]
    add  esp, 28
    ret
