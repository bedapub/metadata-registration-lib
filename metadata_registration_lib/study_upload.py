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


def add_dataset_to_study(dataset_data, study_id, host, email=None, password=None):
    """
    The main "dataset_data" input should be formated as follow:
    {
        "form_name": form_name,
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

    # Parse dataset data
    prop_name_to_id = map_key_value(endpoints["property"], key="name", value="id")

    dataset_converter = FormatConverter(mapper=prop_name_to_id)
    dataset_converter.add_form_format(dataset_data["entries"])
    dataset_converter.clean_data()

    # Build API friendly data
    dataset_api_data = {
        "form_name": dataset_data["form_name"],
        "entries": dataset_converter.get_api_format(),
        "manual_meta_information": dataset_data.get("manual_meta_information", {})
    }

    # Post dataset
    url = f"{endpoints['study']}/id/{study_id}/datasets"
    dataset_res = requests.post(url=url, json=dataset_api_data, headers=headers)

    if dataset_res.status_code != 201:
        raise Exception(f"Fail to add dataset to study. {dataset_res.json()}")

    dataset_uuid = dataset_res.json()["uuid"]
    print(f"Successfully added dataset to study (dataset uuid: {dataset_uuid})")

    return dataset_uuid


def add_process_event_to_dataset(pe_data, study_id, dataset_uuid, host, email=None, password=None):
    """
    The main "pe_data" input should be formated as follow:
    {
        "form_name": form_name,
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

    # Parse processing event data
    prop_name_to_id = map_key_value(endpoints["property"], key="name", value="id")

    pe_converter = FormatConverter(mapper=prop_name_to_id)
    pe_converter.add_form_format(pe_data["entries"])
    pe_converter.clean_data()

    # Build API friendly data
    pe_api_data = {
        "form_name": pe_data["form_name"],
        "entries": pe_converter.get_api_format(),
        "manual_meta_information": pe_data.get("manual_meta_information", {})
    }

    # Post processing event
    url = f"{endpoints['study']}/id/{study_id}/datasets/id/{dataset_uuid}/pes"
    pe_res = requests.post(url=url, json=pe_api_data, headers=headers)

    if pe_res.status_code != 201:
        raise Exception(f"Fail to add processing event to dataset. {pe_res.json()}")

    pe_uuid = pe_res.json()["uuid"]
    print(f"Successfully added processing event to dataset (id: {pe_uuid})")

    return pe_uuid

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

