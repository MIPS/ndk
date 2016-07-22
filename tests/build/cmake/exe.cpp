extern "C" {
#include "shared.h"
#include "static.h"
}

#if defined(NONE)
#include <stdio.h>
#else
#include <cstdio>
#endif

#if !defined(NONE) && !defined(SYSTEM)
#include "shared.hpp"
#include "static.hpp"
#include <iostream>
#endif

int main() {
	printf("%s\n", shared_get_string());
	printf("%s\n", static_get_string());
#if !defined(NONE) && !defined(SYSTEM)
	std::cout
		<< shared_get_string() << std::endl
		<< static_get_string() << std::endl
		<< Shared().GetString() << std::endl
		<< Static().GetString() << std::endl;
#endif
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
