from collections.abc import MutableMapping
from collections import OrderedDict
from copy import deepcopy


class NormConverter:
    """
    Helper class to convert data normalization
    FORMATS:
        - nested_data
            [
                {
                    "readout_id": "RDT_1",
                    "samples": [
                        {
                            "sample_id": "SAM_1",
                            "treatment": {"treatment_id": "TRE_1"}
                        },
                        {
                            "sample_id": "SAM_2",
                            "treatment": {"treatment_id": "TRE_2"}
                        },
                    ]
                },
                {
                    "readout_id": "RDT_2",
                    "samples": [
                    {
                        "sample_id": "SAM_3",
                        "treatment": {"treatment_id": "TRE_3"}
                    }
                    ]
                }
            ]
        - flat_data_1
            [
                {
                    "readout_id": "RDT_1",
                    "sample_1__sample_id": "SAM_1",
                    "sample_1__treatment__treatment_id": "TRE_1",
                    "sample_2__sample_id": "SAM_2",
                    "sample_2__treatment__treatment_id": "TRE_2",
                }
                {
                    "readout_id": "RDT_2",
                    "sample_1__sample_id": "SAM_3",
                    "sample_1__treatment__treatment_id": "TRE_3",
                }
            ]
        - denorm_data_1
            [
                {
                    "readout_id": "RDT_1",
                    "sample__sample_id": "SAM_1",
                    "sample__treatment__treatment_id": "TRE_1",
                }
                {
                    "readout_id": "RDT_1",
                    "sample__sample_id": "SAM_2",
                    "sample__treatment__treatment_id": "TRE_2",
                }
                {
                    "readout_id": "RDT_2",
                    "sample__sample_id": "SAM_3",
                    "sample__treatment__treatment_id": "TRE_3",
                }
            ]

        - denorm_data_2
            {
                "readout_id": ["RDT_1", "RDT_1", "RDT_2"],
                "sample_id": ["SAM_1", "SAM_2", "SAM_3"],
                "treatment_id": ["TRE_1", "TRE_2", "TRE_3"],
            }
    """

    def __init__(self, nested_data=None, flat_data=None, denorm_data=None):
        self.nested_data = nested_data
        self.flat_data = flat_data
        self.denorm_data = denorm_data

    def get_denorm_data_1_from_nested(
        self, vars_to_denorm, use_parent_key=True, sep=".", initial_parent_key=""
    ):
        if self.nested_data is None:
            raise Exception("'nested_data' needs to be set.")

        if isinstance(self.nested_data, dict):
            input_data = [self.nested_data]
        else:
            input_data = self.nested_data

        self.denorm_data = []

        for d in input_data:
            # 1. Denormalize
            tmp_denorm_data = [d]
            for var in vars_to_denorm:
                new_denorm_data = []
                for tmp_d in tmp_denorm_data:
                    new_denorm_data += denormalize_dict_one_var(tmp_d, var)
                tmp_denorm_data = new_denorm_data
            # 2. Flatten
            for tmp_d in tmp_denorm_data:
                flat_denorm_d = flatten_dict(
                    tmp_d,
                    parent_key=initial_parent_key,
                    sep=sep,
                    use_parent_key=use_parent_key,
                )
                self.denorm_data.append(flat_denorm_d)

        return self.denorm_data

    def get_denorm_data_2_from_nested(
        self,
        vars_to_denorm,
        use_parent_key=True,
        sep=".",
        initial_parent_key="",
        missing_value=None,
    ):
        # 1. Get denormlized flat data
        denorm_data_1 = self.get_denorm_data_1_from_nested(
            vars_to_denorm,
            use_parent_key=use_parent_key,
            sep=sep,
            initial_parent_key=initial_parent_key,
        )

        # 2. Get all possible keys
        keys = set()
        for d in denorm_data_1:
            keys |= set(d.keys())

        keys = sorted(list(keys))

        # 3. Build final dict of list (of equal length)
        self.denorm_data = OrderedDict((k, []) for k in keys)

        for d in denorm_data_1:
            for key in self.denorm_data:
                self.denorm_data[key].append(d.get(key, missing_value))

        return self.denorm_data

    def get_flat_data_1_from_nested(self):
        raise NotImplementedError()

    def get_nested_data_from_flat(self):
        raise NotImplementedError()

    def get_nested_data_from_denorm(self):
        raise NotImplementedError()


def flatten_dict(d, use_parent_key=True, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if (parent_key and use_parent_key) else k
        if isinstance(v, MutableMapping):
            items.extend(
                flatten_dict(
                    v,
                    use_parent_key=use_parent_key,
                    parent_key=new_key,
                    sep=sep,
                ).items()
            )
        else:
            items.append((new_key, v))
    return dict(items)


def denormalize_dict_one_var(d, var):
    """
    Dupplicate dicts expending a specific list
    d = {var=[...], ...}
    """
    results = []
    for value in d[var]:
        sub_d = deepcopy(d)
        sub_d[var] = value
        results.append(sub_d)

    return results
