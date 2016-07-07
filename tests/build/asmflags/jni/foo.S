// ASFLAGS only apply to .S files.
#ifndef LOCAL_ASFLAG
#error "LOCAL_ASFLAGS not passed to .S files."
#endif

#ifndef APP_ASFLAG
#error "APP_ASFLAGS not passed to .S files."
#endif

// CFLAGS apply to all .S, .c, and .cpp files.
#ifndef LOCAL_CFLAG
#error "LOCAL_CFLAGS not passed to .S files."
#endif

#ifndef APP_CFLAG
#error "APP_CFLAGS not passed to .S files."
#endif

// CONLYFLAGS apply to .c files.
#ifdef LOCAL_CONLYFLAG
#error "LOCAL_CONLYFLAGS passed to .S files."
#endif

#ifdef APP_CONLYFLAG
#error "APP_CONLYFLAGS passed to .S files."
#endif

// ASMFLAGS apply to .asm files.
#ifdef LOCAL_ASMFLAG
#error "LOCAL_ASMFLAGS passed to .S files."
#endif

#ifdef APP_ASMFLAG
#error "APP_ASMFLAGS passed to .S files."
#endif
