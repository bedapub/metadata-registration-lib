import unittest

from metadata_registration_lib.other_utils import str_to_bool


class TestSimpleFunctions(unittest.TestCase):
    def test_str_to_bool(self):
        for s in ["true", "1", "yes", "y", "on", "t"]:
            assert str_to_bool(s) == True

        for s in ["n", "0", "None", "off", "f", ""]:
            assert str_to_bool(s) == False
