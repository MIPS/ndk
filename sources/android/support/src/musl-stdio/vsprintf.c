#include <stdio.h>
#include <limits.h>

int vsprintf(char *restrict s, const char *restrict fmt, va_list ap) __overloadable
{
	return vsnprintf(s, INT_MAX, fmt, ap);
}
