#include <strings.h>

#if !defined(__LP64__) && __ANDROID_API__ >= 18
#error Test misconfigured or minimum API is now 18
#error In the latter case please remove legacy_strings_inlines.h from bionic.
#endif

int main(int argc, char* argv[]) {
  return ffs(argc);
}
