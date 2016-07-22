#if defined(NONE)
#include <cstdio>
#else
#include <stdio.h>
#endif

#if !defined(NONE) && !defined(SYSTEM)
#include <iostream>
#endif

int main() {
	printf("Hello world!\n");

#if !defined(NONE) && !defined(SYSTEM)
	std::cout << "Hello world from the STL!\n" << std::endl;
#endif
}
