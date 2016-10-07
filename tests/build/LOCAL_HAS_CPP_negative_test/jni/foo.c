// https://github.com/android-ndk/ndk/issues/205
// This test is verifying that LOCAL_HAS_CPP defaults to off.
//
// To test that this is working, we define an extern for `std::terminate` and
// call it in a C file. Without `LOCAL_HAS_CPP := true`, this module would fail
// to link because it wouldn't be able to find `std::terminate`. This test is
// configured to expect build failure.
extern void _ZSt9terminatev();
void terminate() {
  _ZSt9terminatev();
}
