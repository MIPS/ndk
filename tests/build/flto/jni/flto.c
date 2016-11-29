extern void bar();

int foo() {
    bar();
    return 0;
}

int main()
{
    return foo();
}
