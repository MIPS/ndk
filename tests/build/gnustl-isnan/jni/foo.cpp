// Intentionally including both of these is absurd, but including math.h instead
// of cmath is very common, and the stdlib will use cmath, so both are commonly
// included.
// https://code.google.com/p/android/issues/detail?id=271629
#include <math.h>
#include <cmath>

int main(int argc, char** argv) {
  ::isnan(0.0);
  return 0;
}
