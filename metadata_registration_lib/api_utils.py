import requests
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


def map_key_value(url, key="id", value="name"):
    """Call API at url endpoint and create a dict which maps key to value

    If the response contains identical keys, only the last value is stored for this key. The mapping only works
    for fields in the top level (no nested fields).

    :param url: API endpoint to call
    :type url: str
    :param key: The key by which the value will be found
    :type key: str
    :param value: The value to which the key will map
    :type value: str
    ...
    :return: A dict with maps key -> value
    :rtype: dict

    """
    res = requests.get(url, headers={"x-Fields": f"{key}, {value}"})

    if res.status_code != 200:
        raise Exception(f"Request to {url} failed with key: {key} and value: {value}. {res.json()}")

    return {entry[key]: entry[value] for entry in res.json()}


def get_form_by_name(name, form_endpoint):
    header = {"X-Fields": "name, id"}
    forms_res = requests.get(form_endpoint, headers=header)

    if forms_res.status_code != 200:
        raise Exception(f"Fail to load all forms [{forms_res.status_code}] {forms_res.json()}")

    try:
        form_entry = next(filter(lambda entry: entry["name"] == name, forms_res.json()))
        form_json = requests.get(f"{form_endpoint}/id/{form_entry['id']}").json()
        parser = JsonFlaskParser()
        form_class = parser.to_form(form_json)[1]
        return {"class": form_class, "json": form_json}

    except StopIteration:
        raise Exception(f"Fail to find form in database (name:{name})")


def unexpend_json_properties(json_obj):
    """
    Function to replace extended "propery" dict by the id only
    """
    for k, v in json_obj.items():
        if k == "property" and isinstance(v, dict):
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

    def __init__(self, mapper: dict, key_name: str = "property", value_name: str = "value"):
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
        return f"<{self.__class__.__name__} (key name: {self.key_name}, value name: {self.value_name}, " \
               f"mapper: {self.mapper})>"

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
        self.entries = [Entry(self).add_form_format(key=key, value=value) for key, value in data.items()]
        return self

    def get_api_format(self):
        """
        :return: Returns data in api format
        """
        return [{self.key_name: entry.prop_id, self.value_name: entry.get_api_format()} for entry in self.entries]

    def get_form_format(self):
        """
        :return: Returns data in form format
        """
        return {entry.prop_name: entry.get_form_format() for entry in self.entries}


class Entry:

    def __init__(self, converter):
        self.converter = converter

        self.prop_id = None
        self.prop_name = None
        self.value = None

    def __repr__(self):
        return f"<Entry(property: {self.prop_name}, id: {self.prop_id}, value: {self.value})>"

    def add_api_format(self, data):
        self.prop_id = data[self.converter.key_name]
        self.prop_name = self.converter.mapper[self.prop_id]

        def convert_value(value):
            if type(value) in PRIMITIVES:  # simple value
                return value
            elif isinstance(value, list):
                if all(type(entry) in PRIMITIVES for entry in value):  # list of simple values
                    return value
                elif all(isinstance(entry, dict) for entry in value):  # FormField
                    return NestedEntry(self.converter).add_api_format(value)
                elif all(isinstance(entry, list) for entry in value):  # FieldList of FormField
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
                    return value
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
        self.value = [Entry(self.converter).add_form_format(key=key, value=value)
                      for key, value in data.items()]
        return self

    def get_api_format(self):
        return [{self.converter.key_name: entry.prop_id, self.converter.value_name: entry.get_api_format()}
                for entry in self.value]

    def get_form_format(self):
        return {entry.prop_name: entry.get_form_format() for entry in self.value}


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
        self.value = [NestedEntry(self.converter).add_form_format(item) for item in data]
        return self

    def get_api_format(self):
        return [entry.get_api_format() for entry in self.value]

    def get_form_format(self):
        return [entry.get_form_format() for entry in self.value]

