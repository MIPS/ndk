#include "shared.h"
#include "static.h"
#include <stdio.h>

int main() {
	printf("%s\n", shared_get_string());
	printf("%s\n", static_get_string());
	return 0;
}

#include <dlfcn.h>
#include <math.h>
#include <stdlib.h>

void link() {
	// Test if libm is linked.
	double sin_zero = sin(0.0);

	// Test if libdl is linked.
	const char *error = dlerror();

	// Test if libc is linked.
	printf("%lf %s\n", sin_zero, error);
}
