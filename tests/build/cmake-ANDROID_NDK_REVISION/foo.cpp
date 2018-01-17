#include <android/ndk-version.h>

#if __NDK_MAJOR__ != NDK_MAJOR_FROM_CMAKE
#error __NDK_MAJOR__ != NDK_MAJOR_FROM_CMAKE
#endif

#if __NDK_MINOR__ != NDK_MINOR_FROM_CMAKE
#error __NDK_MINOR__ != NDK_MINOR_FROM_CMAKE
#endif

#if __NDK_BETA__ != NDK_BETA_FROM_CMAKE
#error __NDK_BETA__ != NDK_BETA_FROM_CMAKE
#endif

#if __NDK_BUILD__ != NDK_BUILD_FROM_CMAKE
#error __NDK_BUILD__ != NDK_BUILD_FROM_CMAKE
#endif

int main() {}
