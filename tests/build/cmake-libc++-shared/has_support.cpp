#include <stdlib.h>

int main() {
  wchar_t ws[7];
  return mbtowc(ws, "foobar", sizeof(ws)) != 6;
}
