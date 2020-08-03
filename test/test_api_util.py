import unittest

from metadata_registration_lib.api_utils import (FormatConverter,
    unexpend_json_properties)

class TestSimpleFunctions(unittest.TestCase):

    def test_unexpend_json_properties(self):
        input_data = {
            "key_1": "value_1",
            "key_2": 123,
            "key_3": [
                {
                    "key_1": "value_1",
                    "key_2": 123,
                    "property": {
                        "id": "5e59341a08a7b2ec0319cda1",
                        "label": "xxxxx",
                        "name": "xxxxx",
                        "level": "xxxxx",
                        "value_type": {
                            "data_type": "text",
                            "controlled_vocabulary": {
                                "description": "xxxxx",
                                "deprecated": False
                            }
                        },
                        "deprecated": False
                    },
                }
            ],
        }

        expected_output = {
            "key_1": "value_1",
            "key_2": 123,
            "key_3": [
                {
                    "key_1": "value_1",
                    "key_2": 123,
                    "property": "5e59341a08a7b2ec0319cda1"
                }
            ]
        }

        self.assertEqual(unexpend_json_properties(input_data), expected_output)


class TestFormatConverter(unittest.TestCase):

    def test_api_to_form_format_case_1(self):
        """Simple value"""
        mapper = {"1": "username"}

        input_format = [
            {
                "prop": "1",
                "value": "Edward"
            }
        ]

        expected_form_format = {"username": "Edward"}

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        actual_form_format = c.add_api_format(input_format).get_form_format()

        self.assertEqual(expected_form_format, actual_form_format)

    def test_api_to_form_format_case_2(self):
        """List of simple values"""
        mapper = {"1": "username"}

        input_format = [
            {
                "prop": "1",
                "value": ["Edward", "Annie"]
            }
        ]

        expected_form_format = {"username": ["Edward", "Annie"]}

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        actual_form_format = c.add_api_format(input_format).get_form_format()

        self.assertEqual(expected_form_format, actual_form_format)

    def test_api_to_form_format_case_3(self):
        """A nested form field. Only one form field is accepted"""
        mapper = {"1": "storage", "2": "location", "3": "number_of_files"}

        input_format = [
            {
                "prop": "1",
                "value": [
                    {"prop": "2", "value": "C:/Documents"},
                    {"prop": "3", "value": 1000}
                ]
            }
        ]

        expected_form_format = {
            "storage": {
                "location": "C:/Documents", "number_of_files": 1000
            }
        }

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        actual_form_format = c.add_api_format(input_format).get_form_format()

        self.assertEqual(expected_form_format, actual_form_format)

    def test_api_to_form_format_case_4(self):
        """List of nested form fields. Each form field is incorporated into a list"""
        mapper = {"1": "contacts", "3": "name", "4": "phone"}

        input_format = [
            {
                "prop": "1",
                "value": [
                    [
                        {"prop": "3", "value": "Edward"},
                        {"prop": "4", "value": "903 367 2072"}
                    ],
                    [
                        {"prop": "3", "value": "Annie"},
                        {"prop": "4", "value": "731 222 8842"}
                    ]
                ],
            }
        ]

        expected_form_format = {
            "contacts": [
                {
                    "name": "Edward", "phone": "903 367 2072"
                },
                {
                    "name": "Annie", "phone": "731 222 8842"
                }
            ]
        }

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        actual_form_format = c.add_api_format(input_format).get_form_format()

        self.assertEqual(expected_form_format, actual_form_format)

    def test_api_to_api_format_case_1(self):
        """Simple value"""
        mapper = {"1": "username"}

        input_format = [
            {
                "prop": "1",
                "value": "Edward"
            }
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        reconstructed_api_format = c.add_api_format(input_format).get_api_format()

        self.assertEqual(input_format, reconstructed_api_format)

    def test_api_to_api_format_case_2(self):
        """List of simple values"""
        mapper = {"1": "username"}

        input_format = [
            {
                "prop": "1",
                "value": ["Edward", "Annie"]
            }
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        reconstructed_api_format = c.add_api_format(input_format).get_api_format()

        self.assertEqual(input_format, reconstructed_api_format)

    def test_api_to_api_format_case_3(self):
        """A nested form field. Only one form field is accepted"""
        mapper = {"1": "storage", "2": "location", "3": "number_of_files"}

        input_format = [
            {
                "prop": "1",
                "value": [
                    {"prop": "2", "value": "C:/Documents"},
                    {"prop": "3", "value": 1000}
                ]
            }
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        reconstructed_api_format = c.add_api_format(input_format).get_api_format()

        self.assertEqual(input_format, reconstructed_api_format)

    def test_api_to_api_format_case_4(self):
        """List of nested form fields. Each form field is incorporated into a list"""
        mapper = {"1": "contacts", "3": "name", "4": "phone"}

        input_format = [
            {
                "prop": "1",
                "value": [
                    [
                        {"prop": "3", "value": "Edward"},
                        {"prop": "4", "value": "903 367 2072"}
                    ],
                    [
                        {"prop": "3", "value": "Annie"},
                        {"prop": "4", "value": "731 222 8842"}
                    ]
                ],
            }
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        reconstructed_input_format = c.add_api_format(input_format).get_api_format()

        self.assertEqual(input_format, reconstructed_input_format)

    def test_form_to_api_form_format_case_1(self):
        mapper = {"username": "1"}

        form_format = {"username": "Edward"}

        expected_api_format = [
            {
                "prop": "1",
                "value": "Edward"
            }
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        actual_api_format = c.add_form_format(form_format).get_api_format()

        self.assertEqual(expected_api_format, actual_api_format)

    def test_form_to_api_format_case_2(self):
        mapper = {"username": "1"}

        form_format = {"username": ["Edward", "Annie"]}

        expected_api_format = [
            {
                "prop": "1",
                "value": ["Edward", "Annie"]
            }
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        actual_api_format = c.add_form_format(form_format).get_api_format()

        self.assertEqual(expected_api_format, actual_api_format)

    def test_form_to_api_format_case_3(self):
        mapper = {"storage": "1", "location": "2", "number_of_files": "3"}

        form_format = {
            "storage": {
                "location": "C:/Documents", "number_of_files": 1000
            }
        }

        expected_api_format = [
            {
                "prop": "1",
                "value": [
                    {"prop": "2", "value": "C:/Documents"},
                    {"prop": "3", "value": 1000}
                ]
            }
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        actual_api_format = c.add_form_format(form_format).get_api_format()

        self.assertEqual(expected_api_format, actual_api_format)

    def test_form_to_api_format_case_4(self):
        mapper = {"contacts": "1", "name": "3", "phone": "4"}

        form_format = {
            "contacts": [
                {
                    "name": "Edward", "phone": "903 367 2072"
                },
                {
                    "name": "Annie", "phone": "731 222 8842"
                }
            ]
        }

        actual_api_format = [
            {
                "prop": "1",
                "value": [
                    [
                        {"prop": "3", "value": "Edward"},
                        {"prop": "4", "value": "903 367 2072"}
                    ],
                    [
                        {"prop": "3", "value": "Annie"},
                        {"prop": "4", "value": "731 222 8842"}
                    ]
                ],
            }
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        expected_api_format = c.add_form_format(form_format).get_api_format()

        self.assertEqual(expected_api_format, actual_api_format)

    def test_get_entry_by_name(self):
        """Get an entry based on its prop_name"""
        mapper = {"1": "username", "2": "phone"}

        input_format = [
            {"prop": "1", "value": "Edward"},
            {"prop": "2", "value": "+33(0)123456789"}
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        c.add_api_format(input_format)

        self.assertEqual(c.get_entry_by_name("username").value, "Edward")


class TestNestedEntry(unittest.TestCase):

    def test_get_entry_by_name(self):
        """Get an entry based on its prop_name"""
        mapper = {"1": "user", "2": "username", "3": "phone"}

        input_format = [
            {"prop": "1", "value": [
                {"prop": "2", "value": "Edward"},
                {"prop": "3", "value": "+33(0)123456789"}
            ]}
        ]

        c = FormatConverter(key_name="prop", value_name="value", mapper=mapper)
        c.add_api_format(input_format)
        user_entry = c.entries[0]

        self.assertEqual(user_entry.value.get_entry_by_name("username").value, "Edward")