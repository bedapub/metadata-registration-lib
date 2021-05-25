import unittest

from metadata_registration_lib.sample_utils import StepTreatmentsInd, StepsSamples


class TestSimpleFunctions(unittest.TestCase):
    def test_jexcel_data_to_id_form_format(self):
        # Hard to test with nested "obj_required" because it uses flask session
        step = StepTreatmentsInd()
        steps_sample = StepsSamples()
        step.prop_name_for_tmp_id = "prop_1"
        step.entity_set.jexcel_data = [["T1", "some_value"], ["T2", "some_value_2"]]
        step.entity_set.prop_names = ["prop_1", "prop_2"]

        expected_output = {
            "T1": {"prop_1": "T1", "prop_2": "some_value"},
            "T2": {"prop_1": "T2", "prop_2": "some_value_2"},
        }

        step.set_id_form_format_from_jexcel_data(
            form_fields=["prop_1", "prop_2"], sample_steps=steps_sample
        )
        actual_output = step.entity_set.id_to_form_format

        assert "uuid" in actual_output["T1"]
        del actual_output["T1"]["uuid"]

        assert "uuid" in actual_output["T2"]
        del actual_output["T2"]["uuid"]

        assert dict(actual_output) == expected_output