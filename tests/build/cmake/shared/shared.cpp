#include "shared.hpp"

#include <string>

Shared::Shared() : str("This is a C++ string from a shared library.") {}

std::string
Shared::GetString() {
	return str;
}
