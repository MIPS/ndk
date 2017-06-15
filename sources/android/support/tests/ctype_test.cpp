#include <ctype.h>

#include <gtest/gtest.h>

TEST(ctype, isblank) {
  ASSERT_TRUE(isblank(' '));
  ASSERT_TRUE(isblank('\t'));
  ASSERT_FALSE(isblank('\n'));
  ASSERT_FALSE(isblank('\f'));
  ASSERT_FALSE(isblank('\r'));
}

TEST(ctype, isprint) {
  ASSERT_TRUE(isprint('a'));
  ASSERT_TRUE(isprint(' '));
  ASSERT_FALSE(isprint('\t'));
  ASSERT_FALSE(isprint('\n'));
  ASSERT_FALSE(isprint('\f'));
  ASSERT_FALSE(isprint('\r'));
}
