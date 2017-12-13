APP_STL := stlport_static
APP_MODULES := \
    gtest-filepath_test \
    gtest-linked_ptr_test \
    gtest-listener_test \
    gtest-message_test \
    gtest-options_test \
    gtest-param-test_test \
    gtest-port_test \
    gtest-printers_test \
    gtest-test-part_test \
    gtest-typed-test_test \
    gtest-unittest-api_test \
    gtest_environment_test \
    gtest_main_unittest \
    gtest_no_test_unittest \
    gtest_pred_impl_unittest \
    gtest_premature_exit_test \
    gtest_prod_test \
    gtest_repeat_test \
    gtest_sole_header_test \
    gtest_stress_test \
    gtest_unittest \

# Test is disabled until https://github.com/google/googletest/pull/728 lands.
# APP_MODULES += gtest-death-test_test
