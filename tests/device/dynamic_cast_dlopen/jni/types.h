#pragma once

class MyType {
public:
  virtual ~MyType(){};
};

class MyTypeImpl : public MyType {
public:
  MyTypeImpl();
};
