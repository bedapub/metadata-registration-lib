import unittest

from metadata_registration_lib.data_utils import (
    flatten_dict,
    denormalize_dict_one_var,
    NormConverter,
    expand_json_strings,
)


class TestFlatten(unittest.TestCase):
    def test_flatten_dict_pk(self):
        input_data = {"a": 1, "c": {"a": 2, "b": {"x": 5, "y": 10}}, "d": [1, 2, 3]}
        expected_output = {"a": 1, "c.a": 2, "c.b.x": 5, "d": [1, 2, 3], "c.b.y": 10}
        output = flatten_dict(input_data, use_parent_key=True, sep=".")
        self.assertEqual(output, expected_output)

    def test_flatten_dict_no_pk(self):
        # Unique keys
        input_data = {"a": 1, "b": {"c": 2, "d": {"e": 5, "f": 10}}, "g": [1, 2, 3]}
        expected_output = {"a": 1, "c": 2, "e": 5, "f": 10, "g": [1, 2, 3]}
        output = flatten_dict(input_data, use_parent_key=False)
        self.assertEqual(output, expected_output)

        # Non unique keys
        input_data = {"a": 1, "c": {"a": 2, "b": {"x": 5, "y": 10}}, "d": [1, 2, 3]}
        expected_output = {"a": 2, "d": [1, 2, 3], "x": 5, "y": 10}
        output = flatten_dict(input_data, use_parent_key=False)
        self.assertEqual(output, expected_output)


class TestDenormalize(unittest.TestCase):
    def test_denormalize_dict_one_var(self):
        input_data = {"a": 1, "b": 2, "c": [31, 32], "d": [41, 42]}
        expected_output = [
            {"a": 1, "b": 2, "c": 31, "d": [41, 42]},
            {"a": 1, "b": 2, "c": 32, "d": [41, 42]},
        ]
        output = denormalize_dict_one_var(input_data, "c")
        self.assertEqual(output, expected_output)


class TestNormConverter(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_data = [
            {
                "a": 11,
                "b": {"c": 21, "d": {"e": 31, "f": 41}},
                "g": [{"g1": 511, "g2": 611}, {"g1": 512, "g2": 612}],
            },
            {
                "a": 12,
                "b": {"c": 22, "d": {"e": 32, "f": 42}},
                "g": [{"g1": 521, "g2": 621}, {"g1": 522, "g2": 622}],
            },
        ]

    def test_get_denorm_data_1_from_nested(self):
        expected_output = [
            {"a": 11, "b.c": 21, "b.d.e": 31, "b.d.f": 41, "g.g1": 511, "g.g2": 611},
            {"a": 11, "b.c": 21, "b.d.e": 31, "b.d.f": 41, "g.g1": 512, "g.g2": 612},
            {"a": 12, "b.c": 22, "b.d.e": 32, "b.d.f": 42, "g.g1": 521, "g.g2": 621},
            {"a": 12, "b.c": 22, "b.d.e": 32, "b.d.f": 42, "g.g1": 522, "g.g2": 622},
        ]
        converter = NormConverter(nested_data=self.input_data)
        output = converter.get_denorm_data_1_from_nested(
            vars_to_denorm=["g"], use_parent_key=True
        )
        self.assertEqual(output, expected_output)

    def test_get_denorm_data_1_from_nested_no_pk(self):
        expected_output = [
            {"a": 11, "c": 21, "e": 31, "f": 41, "g1": 511, "g2": 611},
            {"a": 11, "c": 21, "e": 31, "f": 41, "g1": 512, "g2": 612},
            {"a": 12, "c": 22, "e": 32, "f": 42, "g1": 521, "g2": 621},
            {"a": 12, "c": 22, "e": 32, "f": 42, "g1": 522, "g2": 622},
        ]
        converter = NormConverter(nested_data=self.input_data)
        output = converter.get_denorm_data_1_from_nested(
            vars_to_denorm=["g"], use_parent_key=False
        )
        self.assertEqual(output, expected_output)

    def test_get_denorm_data_2_from_nested(self):
        expected_output = {
            "a": [11, 11, 12, 12],
            "b.c": [21, 21, 22, 22],
            "b.d.e": [31, 31, 32, 32],
            "b.d.f": [41, 41, 42, 42],
            "g.g1": [511, 512, 521, 522],
            "g.g2": [611, 612, 621, 622],
        }

        converter = NormConverter(nested_data=self.input_data)
        output = converter.get_denorm_data_2_from_nested(
            vars_to_denorm=["g"], use_parent_key=True, missing_value=None
        )
        self.assertEqual(output, expected_output)


class TestJson(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_data = {
            "a": 123,
            "b": {
                "a": "abc",
                "user_defined_json_data": '{"aaa":123, "bbb":"abc"}',
            },
            "user_defined_json_data": '{"aaa":456, "bbb":"def"}',
        }

    def test_expand_json_strings(self):
        expected_output = {
            "a": 123,
            "b": {"a": "abc", "aaa": 123, "bbb": "abc"},
            "aaa": 456,
            "bbb": "def",
        }
        output = expand_json_strings(self.input_data)
        self.assertEqual(output, expected_output)
