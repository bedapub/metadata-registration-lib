from urllib.parse import urljoin
import requests

from api_utils import (map_key_value, login_and_get_header,
    FormatConverter)

def post_study(study_data, host, email=None, password=None):
    """
    The main "study_data" input should be formated as follow:
    {
        "form_name": form_name,
        "initial_state": supported_initial_state,
        "manual_meta_information": {"user": user_name}
        "entries": {
            property_name: value,
            property_name: value,
            property_name: [value1, value2, ...],
            property_name: [
                {
                    property_name: value,
                    property_name: value,
                }
            ]
        }
    }
    """
    endpoints = get_endpoints(host)

    # Get authentification token
    headers = login_and_get_header(
        login_url = endpoints["login"],
        use_token = True,
        email = email,
        password = password
    )

    # Parse study data
    prop_name_to_id = map_key_value(endpoints["property"], key="name", value="id")

    study_converter = FormatConverter(mapper=prop_name_to_id)
    study_converter.add_form_format(study_data["entries"])
    study_converter.clean_data()

    # Build API friendly data
    study_api_data = {
        "form_name": study_data["form_name"],
        "initial_state": study_data["initial_state"],
        "entries": study_converter.get_api_format(),
        "manual_meta_information": study_data.get("manual_meta_information", {})
    }

    # Post study
    study_res = requests.post(url=endpoints["study"], json=study_api_data, headers=headers)

    if study_res.status_code != 201:
        raise Exception(f"Fail to add study. {study_res.json()}")

    study_info = f"(study_id: {study_data['entries']['study_id']}, id: {study_res.json()['id']})"

    print(f"Successfully registered study " + study_info)

    return study_res.json()["id"]


# def add_dataset_to_study(dataset_data, study_id, host, email=None, password=None):
#     """
#     The main "dataset_data" input should be formated as follow:
#     {
#         "form_name": form_name,
#         "manual_meta_information": {"user": user_name}
#         "entries": {
#             property_name: value,
#             property_name: value,
#             property_name: [value1, value2, ...],
#             property_name: [
#                 {
#                     property_name: value,
#                     property_name: value,
#                 }
#             ]
#         }
#     }
#     """
#     endpoints = get_endpoints(host)

#     prop_name_to_id = map_key_value(endpoints["property"], key="name", value="id")
#     prop_id_to_name = map_key_value(endpoints["property"], key="id", value="name")

#     # Get authentification token
#     headers = login_and_get_header(endpoints["login"], email, password)

#     # Get study we want to append a dataset to
#     study_json = api_get(f"{endpoints['study']}/id/{study_id}")

#     # Generates dataset UUID
#     if not "uuid" in dataset_data["entries"]:
#         dataset_data["entries"]["uuid"] = str(uuid.uuid1())

#     # Convert from "form" format to "entries" API friendly format
#     form_json = get_form_json_by_name(endpoints["form"], dataset_data["form_name_construction"])

#     dataset_entryset = EntrySet()
#     dataset_entryset.set_entries_from_simple_format(
#         data = dataset_data["entries"],
#         form_json = form_json,
#         map = prop_name_to_id
#     )
#     dataset_entryset.clean_data()

#     # In the next steps, we modify chained references to objects that are actually
#     # in the study entries at the start. Since we're editing different references 
#     # to the same mutable objects, it works (seems dodgy though)

#     # Check if "datasets" entry already exist study, creates it if it doesn't
#     study_entryset = EntrySet()
#     study_entryset.set_entries_from_api_format(study_json["entries"], prop_id_to_name)

#     datasets_entry = study_entryset.get_entry_by_name("datasets")

#     if datasets_entry is not None:
#         datasets_entry.value.append(dataset_entryset.entries)
#     else:
#         study_entryset.entries.append(StudyEntry(
#             identifier = prop_name_to_id["datasets"],
#             name = "datasets",
#             value = [dataset_entryset.entries]
#         ))

#     study_json["entries"] = study_entryset.api_format()
#     study_json["form_name"] = dataset_data["form_name"]
#     study_json["manual_meta_information"] = dataset_data.get("manual_meta_information", {})

#     # Post study
#     study_res = requests.put(url=f"{endpoints['study']}/id/{study_id}", json=study_json, headers=headers)

#     if study_res.status_code != 200:
#         raise Exception(f"Fail to update study. {study_res.json()}")

#     study_info = f"(dataset_id: {dataset_data['entries']['dataset_id']}, id: {dataset_data['entries']['uuid']})"

#     print(f"Successfully added dataset to study " + study_info)

#     return dataset_data['entries']['uuid']


# def add_process_event_to_dataset(pe_data, study_id, dataset_uuid, host, email=None, password=None):
#     """
#     The main "pe_data" input should be formated as follow:
#     {
#         "form_name": form_name,
#         "manual_meta_information": {"user": user_name}
#         "entries": {
#             property_name: value,
#             property_name: value,
#             property_name: [value1, value2, ...],
#             property_name: [
#                 {
#                     property_name: value,
#                     property_name: value,
#                 }
#             ],
#         }
#     }
#     """
#     endpoints = get_endpoints(host)

#     prop_name_to_id = map_key_value(endpoints["property"], key="name", value="id")
#     prop_id_to_name = map_key_value(endpoints["property"], key="id", value="name")

#     # Get authentification token
#     headers = login_and_get_header(endpoints["login"], email, password)

#     # Get study we want to append a dataset to
#     study_json = api_get(f"{endpoints['study']}/id/{study_id}")

#     # Generates PE UUID
#     if not "uuid" in pe_data["entries"]:
#         pe_data["entries"]["uuid"] = str(uuid.uuid1())

#     # Convert from "form" format to "entries" API friendly format
#     form_json = get_form_json_by_name(endpoints["form"], pe_data["form_name_construction"])

#     pe_entryset = EntrySet()
#     pe_entryset.set_entries_from_simple_format(
#         data = pe_data["entries"],
#         form_json = form_json,
#         map = prop_name_to_id
#     )
#     pe_entryset.clean_data()

#     # In the next steps, we modify chained references to objects that are actually
#     # in the study entries at the start. Since we're editing different references 
#     # to the same mutable objects, it works (seems dodgy though)

#     # Recreate study entries and find dataset
#     study_entryset = EntrySet()
#     study_entryset.set_entries_from_api_format(study_json["entries"], prop_id_to_name)

#     datasets_entry = study_entryset.get_entry_by_name("datasets")
#     dataset_entries, dataset_position = datasets_entry.find_nested_formfield_entry("uuid", dataset_uuid)
#     dataset_entryset = EntrySet(entries=dataset_entries)

#     # Check if "process_events" entry already exists and create if if it doesn't
#     pe_entry = dataset_entryset.get_entry_by_name("process_events")
#     if pe_entry is not None:
#         pe_entry.value.append(pe_entryset.entries)
#     else:
#         dataset_entryset.entries.append(StudyEntry(
#             identifier = prop_name_to_id["process_events"],
#             name = "process_events",
#             value = [pe_entryset.entries]
#         ))

#     datasets_entry.value[dataset_position] = dataset_entryset.entries
#     study_json["entries"] = study_entryset.api_format()
#     study_json["form_name"] = pe_data["form_name"]
#     study_json["manual_meta_information"] = pe_data.get("manual_meta_information", {})

#     # Post study
#     study_res = requests.put(url=f"{endpoints['study']}/id/{study_id}", json=study_json, headers=headers)

#     if study_res.status_code != 200:
#         raise Exception(f"Fail to update study. {study_res.json()}")

#     study_info = f"(id: {pe_data['entries']['uuid']})"

#     print(f"Successfully added dataset to study " + study_info)

#     return pe_data['entries']['uuid']

###########################################
######## Helper functions
###########################################
def get_endpoints(host):
    return {
        "study": urljoin(host, "studies"),
        "property": urljoin(host, "properties"),
        "form": urljoin(host, "forms"),
        "login": urljoin(host, "users/login")
    }

def api_get(url):
    obj_res = requests.get(url=url)

    if obj_res.status_code != 200:
        raise Exception(f"Failed GET request on {url}. {obj_res.json()}")

    return obj_res.json()

