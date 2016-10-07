// https://github.com/android-ndk/ndk/issues/205
// This test is verifying that we can link the STL even if we don't know about
// any explicit C++ dependencies for the module. `LOCAL_HAS_CPP := true`
// instructs ndk-build to link the STL anyway.
//
// To test that this is working, we define an extern for `std::terminate` and
// call it in a C file. Without `LOCAL_HAS_CPP := true`, this module would fail
// to link because it wouldn't be able to find `std::terminate`.
extern void _ZSt9terminatev();
void terminate() {
  _ZSt9terminatev();
}
