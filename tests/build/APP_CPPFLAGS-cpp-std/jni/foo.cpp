#if defined(__clang__) && __cplusplus != 201402L
#error "__cplusplus != 201402L"
#elif !defined(__clang__) && __cplusplus != 201300L
// GCC is still C++1y.
#error "__cplusplus != 201300L"
#endif
