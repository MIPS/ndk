// ASFLAGS only apply to .S files.
#ifdef LOCAL_ASFLAG
#error "LOCAL_ASFLAGS passed to .c files."
#endif

#ifdef APP_ASFLAG
#error "APP_ASFLAGS passed to .c files."
#endif

// CFLAGS apply to all .S, .c, and .cpp files.
#ifndef LOCAL_CFLAG
#error "LOCAL_CFLAGS not passed to .c files."
#endif

#ifndef APP_CFLAG
#error "APP_CFLAGS not passed to .c files."
#endif

// CONLYFLAGS apply to .c files.
#ifndef LOCAL_CONLYFLAG
#error "LOCAL_CONLYFLAGS not passed to .c files."
#endif

#ifndef APP_CONLYFLAG
#error "APP_CONLYFLAGS passed to .c files."
#endif

// ASMFLAGS apply to .asm files.
#ifdef LOCAL_ASMFLAG
#error "LOCAL_ASMFLAGS passed to .c files."
#endif

#ifdef APP_ASMFLAG
#error "APP_ASMFLAGS passed to .c files."
#endif
