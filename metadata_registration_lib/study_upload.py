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

    # Format and send data to API
    study_id = send_study_nested_entity_to_api(
        data = study_data,
        id_key = "id",
        url = endpoints["study"],
        method = "post",
        endpoints = endpoints,
        email = email,
        password = password
    )

    print(f"Successfully registered study (id = {study_id})")

    return study_id


def add_dataset_to_study(dataset_data, study_id, host, email=None, password=None):
    """
    The main "dataset_data" input should be formated as follow:
    {
        "form_name": form_name,
        "manual_meta_information": {"user": user_name}
        "entries": {
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

    # Format and send data to API
    dataset_uuid = send_study_nested_entity_to_api(
        data = dataset_data,
        id_key = "uuid",
        url = f"{endpoints['study']}/id/{study_id}/datasets",
        method = "post",
        endpoints = endpoints,
        email = email,
        password = password
    )

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

    # Format and send data to API
    pe_uuid = send_study_nested_entity_to_api(
        data = pe_data,
        id_key = "uuid",
        url = f"{endpoints['study']}/id/{study_id}/datasets/id/{dataset_uuid}/pes",
        method = "post",
        endpoints = endpoints,
        email = email,
        password = password
    )

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

def send_study_nested_entity_to_api(data, id_key, url, method, endpoints, email, password):
    """Format and send data to the API (nested study entity data)"""
    # Get authentification token
    headers = login_and_get_header(
        login_url = endpoints["login"],
        use_token = True,
        email = email,
        password = password
    )

    # Format data (cleaning + conversion from "form format" to "api format")
    prop_name_to_id = map_key_value(endpoints["property"], key="name", value="id")

    converter = FormatConverter(mapper=prop_name_to_id)
    converter.add_form_format(data["entries"])
    converter.clean_data()

    # Build API friendly data
    api_data = {
        "form_name": data["form_name"],
        "entries": converter.get_api_format(),
        "manual_meta_information": data.get("manual_meta_information", {})
    }
    if data.get("initial_state") is not None:
        api_data["initial_state"] = data["initial_state"]

    # Send data to API
    if method == "post":
        res = requests.post(url=url, json=api_data, headers=headers)
        if res.status_code != 201:
            raise Exception(f"Fail to POST this nested study entry. {res.json()}")

        return res.json()[id_key]

    elif method == "put":
        res = requests.put(url=url, json=api_data, headers=headers)
        if res.status_code != 200:
            raise Exception(f"Fail to PUT this nested study entry. {res.json()}")

        return True