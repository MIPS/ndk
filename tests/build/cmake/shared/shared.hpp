#ifndef SHARED_HPP
#define SHARED_HPP

#include <string>

class Shared {
	public:
		Shared();
		std::string GetString();
	private:
		std::string str;
};

#endif
