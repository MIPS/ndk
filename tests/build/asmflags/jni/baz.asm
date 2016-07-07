; ASFLAGS only apply to .S files.
%ifdef LOCAL_ASFLAG
%error "LOCAL_ASFLAGS passed to .asm files."
%endif

%ifdef APP_ASFLAG
%error "APP_ASFLAGS passed to .asm files."
%endif

; CFLAGS apply to all .S, .c, and .cpp files.
%ifdef LOCAL_CFLAG
%error "LOCAL_CFLAGS passed to .asm files."
%endif

%ifdef APP_CFLAG
%error "APP_CFLAGS passed to .asm files."
%endif

; CONLYFLAGS apply to .c files.
%ifdef LOCAL_CONLYFLAG
%error "LOCAL_CONLYFLAGS passed to .asm files."
%endif

%ifdef APP_CONLYFLAG
%error "APP_CONLYFLAGS passed to .asm files."
%endif

; ASMFLAGS apply to .asm files.
%ifndef LOCAL_ASMFLAG
%error "LOCAL_ASMFLAGS not passed to .asm files."
%endif

%ifndef APP_ASMFLAG
%error "APP_ASMFLAGS not passed to .asm files."
%endif
