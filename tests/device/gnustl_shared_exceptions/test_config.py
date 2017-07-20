def run_unsupported(abi, device_api, toolchain, subtest):
    if subtest == 'exec_throwing_lib_catching' and device_api < 19:
        # The pre-KitKat linker didn't search the main executable for symbols,
        # so running this test on an older device will result in:
        #
        #     could not load needed library 'libtest2_foo.so' for
        #     './exec_throwing_lib_catching' (reloc_library[1306]:  2349 cannot
        #     locate '_Z3foov'...
        return device_api
    return None
