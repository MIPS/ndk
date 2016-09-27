int main() {
  try {
    throw 0;
    return -1;
  } catch (int ex) {
    return ex;
  }
  return -2;
}
