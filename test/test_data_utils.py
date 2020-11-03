import unittest

from metadata_registration_lib.data_utils import flatten_dict


class TestFlatten(unittest.TestCase):
    def test_flatten_dict(self):
        d = {"a": 1, "c": {"a": 2, "b": {"x": 5, "y": 10}}, "d": [1, 2, 3]}
        expected_output = {"a": 1, "c_a": 2, "c_b_x": 5, "d": [1, 2, 3], "c_b_y": 10}
        self.assertEqual(flatten_dict(d), expected_output)
