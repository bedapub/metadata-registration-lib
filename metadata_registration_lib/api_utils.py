import requests
import uuid
from dynamic_form import JsonFlaskParser

PRIMITIVES = (bool, int, float, str)
PRIMITIVES_LIST = (*PRIMITIVES, list)


def login_and_get_header(login_url, use_token=True, email=None, password=None):
    if use_token and email and password:
        # Retrieve access token
        login_data = {"email": email, "password": password}

        login_res = requests.post(url=login_url, json=login_data)
        if login_res.status_code != 200:
            raise Exception(f"Login to API failed. {login_res.json()}")

        header = login_res.json()
    else:
        print("Access API without access token")
        header = {}

    return header


def map_key_value(url, key="id", value="name", mask=None):
    """Call API at url endpoint and create a dict which maps key to value

    If the response contains identical keys, only the last value is stored for this key. The mapping only works
    for fields in the top level (no nested fields).

    :param url: API endpoint to call
    :type url: str
    :param key: The key by which the value will be found
    :type key: str
    :param value: The value to which the key will map
    :type value: str
    :param mask: Mask string to be used in the x-Fields header of the request
    :type mask: str
    ...
    :return: A dict with maps key -> value
    :rtype: dict

    """
    if mask is None:
        headers = {"x-Fields": f"{key}, {value}"}
    else:
        headers = {"x-Fields": mask}

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        raise Exception(
            f"Request to {url} failed with key: {key} and value: {value}. {res.json()}"
        )

    return {entry[key]: entry[value] for entry in res.json()}


def map_key_value_from_dict_list(dict_list, key, value=None):
    if value is not None:
        return {entry[key]: entry[value] for entry in dict_list}
    else:
        return {entry[key]: entry for entry in dict_list}


def reverse_map(input_map):
    """
    Reverse keys and values of dictionnary
    Input: {k1: v1, k2: v2, ...}
    Output:{v1: k1, v2: k2, ...}
    ...
    :return: A dict with maps value -> key
    :rtype: dict
    """
    return {v: k for k, v in input_map.items()}


def get_prop_name_to_cv_name(property_url):
    prop_name_to_value_type = map_key_value(
        url=property_url,
        key="name",
        value="value_type",
        mask="name, value_type{data_type, controlled_vocabulary{name}}",
    )
    prop_name_to_cv_name = {
        p_name: prop_name_to_value_type[p_name]["controlled_vocabulary"]["name"]
        for p_name in prop_name_to_value_type.keys()
        if prop_name_to_value_type[p_name]["data_type"] == "ctrl_voc"
    }
    return prop_name_to_cv_name


def get_entity_by_name(name, endpoint):
    header = {"X-Fields": "name, id"}
    res = requests.get(endpoint, headers=header)

    if res.status_code != 200:
        raise Exception(f"Fail to load all entities [{res.status_code}] {res.json()}")

    try:
        entity_entry = next(filter(lambda entry: entry["name"] == name, res.json()))
        entity_json = requests.get(f"{endpoint}/id/{entity_entry['id']}").json()
        return entity_json

    except StopIteration:
        raise Exception(f"Fail to find entity in database (name:{name})")


def get_form_by_name(name, form_endpoint):
    form_json = get_entity_by_name(name, form_endpoint)
    parser = JsonFlaskParser()
    form_class = parser.to_form(form_json)[1]
    return {"class": form_class, "json": form_json}


def unexpend_json_properties(json_obj, key_name="property"):
    """
    Function to replace extended "propery" dict by the id only
    """
    for k, v in json_obj.items():
        if k == key_name and isinstance(v, dict):
            json_obj[k] = v["id"]

        elif isinstance(v, dict):
            v = unexpend_json_properties(v)

        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    item = unexpend_json_properties(item)

    return json_obj


class FormatConverter:
    """Class responsible for converting between api format and form format.

    API FORMAT
    ----------
    The api format consists of a list of dictionaries. Each dictionary has two keys: property and value. The value of
    the property is the property id. The second key (value) can take four different formats:
        1. primitive data type (string, int, float, boolean)
        2. list of primitive data types
        3. dictionary (representing a FormField)
        4. list of dictionary (representing a list of FormField)

    FORM FORMAT
    -----------
    The form format is designed such that it can be directly passed to a wtf form. It is a dictionary with the
    property names as key and the given data as value. The value can take four different formats:
        1. primitive data type (string, int, float, boolean)
        2. list of primitive data types
        3. dictionary (representing a FormField)
        4. list of dictionary (representing a list of FormField)
    """

    def __init__(
        self, mapper: dict, key_name: str = "property", value_name: str = "value"
    ):
        """
        :param key_name: name under which the key the property id is stored
        :param value_name: name under which the user input is stored
        :param mapper: dict which converts between the property id and property name
        """
        self.key_name = key_name
        self.value_name = value_name
        self.mapper = mapper

        self.entries = []

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} (key name: {self.key_name}, value name: {self.value_name}, "
            f"mapper: {self.mapper})>"
        )

    def add_api_format(self, data):
        """
        :param data: data in api format
        :return: self
        """
        self.entries = []
        for entry in data:
            self.entries.append(Entry(self).add_api_format(entry))

        return self

    def add_form_format(self, data):
        """
        :param data: data in form format
        :return: self
        """
        self.entries = [
            Entry(self).add_form_format(key=key, value=value)
            for key, value in data.items()
        ]
        return self

    def get_api_format(self):
        """
        :return: Returns data in api format
        """
        return [
            {self.key_name: entry.prop_id, self.value_name: entry.get_api_format()}
            for entry in self.entries
        ]

    def get_form_format(self):
        """
        :return: Returns data in form format
        """
        return {entry.prop_name: entry.get_form_format() for entry in self.entries}

    def get_entry_by_name(self, name):
        for entry in self.entries:
            if entry.prop_name == name:
                return entry
        else:
            return None

    def clean_data(self):
        """
        Clean the value of the entries.
        Check Entry.clean_data to see expected behaviour.
        """
        clean_entries = []
        discarded_entries = []
        for entry in self.entries:
            entry.clean_data()
            if keep_value(entry.value):
                clean_entries.append(entry)
            else:
                discarded_entries.append(entry)

        self.entries = clean_entries
        return discarded_entries

    def add_or_update_entries(self, entries):
        """
        Update the entries with the new values the given entry list.
        If an entry already exists, its value is replaced, if not, it's created.
        """
        current_entries = {e.prop_id: e for e in self.entries}

        for entry in entries:
            if entry.prop_id in current_entries:
                current_entries[entry.prop_id].value = entry.value
            else:
                self.entries.append(entry)
        return self

    def remove_entries(self, entries=None, prop_names=None, prop_ids=None):
        """
        Remove specific entries.
        3 possible input: list of entries, prop_names or prop_ids.
        """
        if len([1 for p in [entries, prop_names, prop_ids] if p is not None]) != 1:
            raise Exception(
                "Please give only one of the following: entries, prop_names, prop_ids"
            )

        if entries is not None:
            to_remove = [e.prop_id for e in entries]
            attribute = "prop_id"
        elif prop_ids is not None:
            to_remove = prop_ids
            attribute = "prop_id"
        elif prop_names is not None:
            to_remove = prop_names
            attribute = "prop_name"

        cleaned_entries = []
        for entry in self.entries:
            if not getattr(entry, attribute) in to_remove:
                cleaned_entries.append(entry)

        self.entries = cleaned_entries
        return self

    def sort_from_form(self, form):
        """
        Sort entries according to the form fields (first level only)

        Priority 1. ID or UUID
        Priority 2. Form fields
        Priority 3. Other fields not present in form (e.g. nested entities)

        :param form: form instance used to define the order of entries
        :return: self
        """
        sorted_entries = []
        used_names = set()

        # Priority 1.
        # Included in forms

        # Priority 2.
        for field in form:
            entry = self.get_entry_by_name(field.name)
            if entry is not None:
                sorted_entries.append(entry)
                used_names.add(field.name)

        # Priority 3.
        for entry in self.entries:
            if not entry.prop_name in used_names:
                sorted_entries.append(entry)

        self.entries = sorted_entries
        return self


class Entry:
    def __init__(self, converter):
        self.converter = converter

        self.prop_id = None
        self.prop_name = None
        self.value = None

    def __repr__(self):
        return f"<Entry(property: {self.prop_name}, id: {self.prop_id}, value: {self.value})>"

    def add_api_format(self, data):
        if isinstance(data[self.converter.key_name], dict):
            self.prop_id = data[self.converter.key_name]["id"]
        else:
            self.prop_id = data[self.converter.key_name]
        self.prop_name = self.converter.mapper[self.prop_id]

        def convert_value(value):
            if type(value) in PRIMITIVES:  # simple value
                return value
            elif isinstance(value, list):
                if all(
                    type(entry) in PRIMITIVES for entry in value
                ):  # list of simple values
                    # No weird format like mongoengine.base.datastructures.BaseList
                    return list(value)
                elif all(isinstance(entry, dict) for entry in value):  # FormField
                    return NestedEntry(self.converter).add_api_format(value)
                elif all(
                    isinstance(entry, list) for entry in value
                ):  # FieldList of FormField
                    return NestedListEntry(self.converter).add_api_format(value)

        self.value = convert_value(data[self.converter.value_name])

        return self

    def add_form_format(self, key, value):
        self.prop_name = key
        self.prop_id = self.converter.mapper[key]

        def convert_value(value):
            if type(value) in PRIMITIVES:
                return value
            elif type(value) is dict:
                return NestedEntry(self.converter).add_form_format(value)
            elif isinstance(value, list):
                if all(type(entry) in PRIMITIVES for entry in value):
                    # No weird format like mongoengine.base.datastructures.BaseList
                    return list(value)
                if all(type(entry) is dict for entry in value):
                    return NestedListEntry(self.converter).add_form_format(value)

        self.value = convert_value(value)

        return self

    def get_api_format(self):
        if type(self.value) in PRIMITIVES_LIST:
            return self.value

        return self.value.get_api_format()

    def get_form_format(self):
        if type(self.value) in PRIMITIVES_LIST:
            return self.value

        return self.value.get_form_format()

    def clean_data(self):
        """
        Clean the value of the entry.
        Decisions:
            - Strings are stripped
            - Empty strings are removed entirely
            - Empty lists are kept
            - Empty dicts are kept
        """
        if type(self.value) in PRIMITIVES:
            self.value = clean_simple_value(self.value)

        elif isinstance(self.value, list):
            clean_values = [clean_simple_value(v) for v in self.value]
            self.value = [v for v in clean_values if keep_value(v)]

        elif isinstance(self.value, NestedEntry):
            for entry in self.value.value:
                entry.clean_data()
            self.value.value = [
                entry for entry in self.value.value if keep_value(entry.value)
            ]

        elif isinstance(self.value, NestedListEntry):
            for nested_entry in self.value.value:
                for entry in nested_entry.value:
                    entry.clean_data()
                nested_entry.value = [
                    entry for entry in nested_entry.value if keep_value(entry.value)
                ]


class NestedEntry:
    def __init__(self, converter):
        self.converter = converter
        self.value = None

    def __repr__(self):
        return f"<{self.__class__.__name__} (value: {self.value})>"

    def add_api_format(self, data):
        self.value = [Entry(self.converter).add_api_format(entry) for entry in data]
        return self

    def add_form_format(self, data):
        self.value = [
            Entry(self.converter).add_form_format(key=key, value=value)
            for key, value in data.items()
        ]
        return self

    def get_api_format(self):
        return [
            {
                self.converter.key_name: entry.prop_id,
                self.converter.value_name: entry.get_api_format(),
            }
            for entry in self.value
        ]

    def get_form_format(self):
        return {entry.prop_name: entry.get_form_format() for entry in self.value}

    def get_entry_by_name(self, name):
        for entry in self.value:
            if entry.prop_name == name:
                return entry
        else:
            return None

    def remove_entries(self, entries=None, prop_names=None, prop_ids=None):
        """
        Remove specific entries.
        3 possible input: list of entries, prop_names or prop_ids.
        """
        if len([1 for p in [entries, prop_names, prop_ids] if p is not None]) != 1:
            raise Exception(
                "Please give only one of the following: entries, prop_names, prop_ids"
            )

        if entries is not None:
            to_remove = [e.prop_id for e in entries]
            attribute = "prop_id"
        elif prop_ids is not None:
            to_remove = prop_ids
            attribute = "prop_id"
        elif prop_names is not None:
            to_remove = prop_names
            attribute = "prop_name"

        cleaned_entries = []
        for entry in self.value:
            if not getattr(entry, attribute) in to_remove:
                cleaned_entries.append(entry)

        self.value = cleaned_entries
        return self


class NestedListEntry:
    def __init__(self, converter):
        self.converter = converter
        self.value = None

    def __repr__(self):
        return f"<{self.__class__.__name__} (value: {self.value})>"

    def add_api_format(self, data):
        self.value = [NestedEntry(self.converter).add_api_format(item) for item in data]
        return self

    def add_form_format(self, data):
        self.value = [
            NestedEntry(self.converter).add_form_format(item) for item in data
        ]
        return self

    def get_api_format(self):
        return [entry.get_api_format() for entry in self.value]

    def get_form_format(self):
        return [entry.get_form_format() for entry in self.value]

    def find_nested_entry(self, name, value):
        """
        Returns a specific nested "NestedEntry" based on the value of one
        of its entries.
        """
        for i, nested_entry in enumerate(self.value):
            entry_data = nested_entry.get_form_format()

            if entry_data[name] == value:
                return nested_entry, i

        raise Exception(f"Nested entry with {name} = '{value}' not found.")

    def delete_nested_entry(self, name, value):
        """
        Deletes a specific nested "NestedEntry" based on the value of one
        of its entries.
        """
        for i, nested_entry in enumerate(self.value):
            entry_data = nested_entry.get_form_format()

            if entry_data[name] == value:
                del self.value[i]
                return i

        raise Exception(f"Nested entry with {name} = '{value}' not found.")


def clean_simple_value(value):
    if isinstance(value, str):
        return value.strip()
    else:
        return value


def keep_value(value):
    if value in ["", None]:
        return False
    else:
        return True


def add_uuid_entry_if_missing(entity_converter, prop_name_to_id, replace=False):
    entry_uuid = entity_converter.get_entry_by_name("uuid")
    if entry_uuid is None:
        new_uuid = str(uuid.uuid1())
        entry_uuid = Entry(FormatConverter(prop_name_to_id)).add_form_format(
            "uuid", new_uuid
        )
        entity_converter.entries.insert(0, entry_uuid)
    elif entry_uuid is not None and replace:
        new_uuid = str(uuid.uuid1())
        entry_uuid.value = new_uuid
    else:
        new_uuid = entry_uuid.value

    return entity_converter, new_uuid


def get_entity_converter(
    entries, entry_format, prop_id_to_name=None, prop_name_to_id=None
):
    if entry_format == "api":
        entity_converter = FormatConverter(mapper=prop_id_to_name)
        entity_converter.add_api_format(entries)
    elif entry_format == "form":
        entity_converter = FormatConverter(mapper=prop_name_to_id)
        entity_converter.add_form_format(entries)

    discarded_entries = entity_converter.clean_data()
    return entity_converter, discarded_entries


def add_entity_to_study_nested_list(
    study_converter,
    entity_converter,
    prop_name_to_id,
    study_list_prop,
):
    entity_nested_entry = NestedEntry(entity_converter)
    entity_nested_entry.value = entity_converter.entries

    # Check if study_list_prop entry already exist study, creates it if it doesn't
    entities_entry = study_converter.get_entry_by_name(study_list_prop)

    if entities_entry is not None:
        entities_entry.value.value.append(entity_nested_entry)
    else:
        entities_entry = Entry(FormatConverter(prop_name_to_id)).add_form_format(
            study_list_prop, [entity_nested_entry.get_form_format()]
        )
        study_converter.entries.append(entities_entry)

    return study_converter