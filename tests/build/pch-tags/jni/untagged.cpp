// Note that ndk-build adds `-include $(LOCAL_PCH)`, so we can be sure that we
// are in fact getting the PCH here by just not including the header. If we tag
// it wrong, the `-include` flag won't be passed.
//
// We can't add the same check to maybe_tagged.cpp because for the case where it
// is a tagged source it specifically will *not* use the PCH.
#ifndef READ_PCH
#error "Did not read precompiled header."
#endif
