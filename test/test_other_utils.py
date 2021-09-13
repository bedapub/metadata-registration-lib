import unittest

from metadata_registration_lib.other_utils import (
    str_to_bool,
    fix_float_issue,
)


class TestSimpleFunctions(unittest.TestCase):
    def test_str_to_bool(self):
        for s in ["true", "1", "yes", "y", "on", "t"]:
            assert str_to_bool(s) == True

        for s in ["n", "0", "None", "off", "f", ""]:
            assert str_to_bool(s) == False

    def test_fix_float_issue(self):
        # Floats with issues
        assert fix_float_issue(0.009600000000000001) == 0.0096
        assert fix_float_issue(0.5599999999999999) == 0.56
        assert fix_float_issue(0.1 + 0.2) == 0.3
        assert fix_float_issue(1000000000.1 + 1000000000.2) == 2000000000.3
        assert fix_float_issue(10000000000.1 + 10000000000.2) == 20000000000.3
        assert fix_float_issue(100000000000.1 + 100000000000.2) == 200000000000.3
        assert fix_float_issue(1000000000000.1 + 1000000000000.2) == 2000000000000.3
        # Floats without issues
        assert fix_float_issue(0.1234) == 0.1234
        assert fix_float_issue(123456.7) == 123456.7
