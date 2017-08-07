#include <math.h>

#include <gtest/gtest.h>

TEST(math, nexttoward) {
    double x = 2.0;
    ASSERT_EQ(x, nexttoward(x, (long double)x));
    ASSERT_LT(x, nexttoward(x, (long double)(x * 2.)));
    ASSERT_GT(x, nexttoward(x, (long double)(x - 1.0)));
}

TEST(math, nexttowardf) {
    float x = 2.0;
    ASSERT_EQ(x, nexttowardf(x, (long double)x));
    ASSERT_LT(x, nexttowardf(x, (long double)(x * 2.)));
    ASSERT_GT(x, nexttowardf(x, (long double)(x - 1.0)));
}

TEST(math, nexttowardl) {
    long double x = 2.0;
    ASSERT_EQ(x, nexttowardl(x, x));
    ASSERT_LT(x, nexttowardl(x, x * 2.));
    ASSERT_GT(x, nexttowardl(x, x - 1.0));
}

// These functions are not exported on x86 before API level 18!
TEST(math, scalbln) {
    ASSERT_EQ(16., scalbln(2.0, (long int)3));
}

TEST(math, scalblnf) {
    ASSERT_EQ((float)16., scalblnf((float)2.0, (long int)3));
}

TEST(math, scalblnl) {
    ASSERT_EQ((long double)16., scalblnl((long double)2.0, (long int)3));
}
