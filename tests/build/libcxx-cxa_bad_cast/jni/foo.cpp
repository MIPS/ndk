struct Foo {
  virtual ~Foo() {}
};

struct Bar {
  virtual ~Bar() {}
};

int main(int argc, char** argv) {
  Foo f;

  try {
    Bar& b = dynamic_cast<Bar&>(f);
  } catch (...) {
  }

  return 0;
}
