from urllib.parse import urljoin
import requests

from metadata_registration_lib.api_utils import (map_key_value,
    login_and_get_header, FormatConverter)

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

    # Get authentification token
    headers = login_and_get_header(
        login_url = endpoints["login"],
        use_token = True,
        email = email,
        password = password
    )

    # Format and send data to API
    study_json, message, success = upload_study_related_entity(
        data = study_data,
        url = endpoints["study"],
        method = "post",
        property_url = endpoints["property"],
        headers = headers
    )

    if success:
        print(f"Successfully registered study (id: {study_json['id']})")
        return study_json["id"]
    else:
        print(f"Error during study upload: {study_json}")
        return None


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

    # Get authentification token
    headers = login_and_get_header(
        login_url = endpoints["login"],
        use_token = True,
        email = email,
        password = password
    )

    # Format and send data to API
    dataset_json, message, success = upload_study_related_entity(
        data = dataset_data,
        url = f"{endpoints['study']}/id/{study_id}/datasets",
        method = "post",
        property_url = endpoints["property"],
        headers = headers
    )

    if success:
        print(f"Successfully added dataset to study (dataset uuid: {dataset_json['uuid']})")
        return dataset_json["uuid"]
    else:
        print(f"Error during dataset upload: {dataset_json}")
        return None


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

    # Get authentification token
    headers = login_and_get_header(
        login_url = endpoints["login"],
        use_token = True,
        email = email,
        password = password
    )

    # Format and send data to API
    pe_json, message, success = upload_study_related_entity(
        data = pe_data,
        url = f"{endpoints['study']}/id/{study_id}/datasets/id/{dataset_uuid}/pes",
        method = "post",
        property_url = endpoints["property"],
        headers = headers
    )

    if success:
        print(f"Successfully added processing event to study (pe uuid: {pe_json['uuid']})")
        return pe_json["uuid"]
    else:
        print(f"Error during processing event upload: {pe_json}")
        return None

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

def upload_study_related_entity(data, url, method, property_url, headers):
    """Send data to the API (study related entity) in form format"""
    entry_format = data.pop("entry_format", "form")

    # Format data (cleaning + conversion from "form format" to "api format")
    if entry_format == "form":
        prop_name_to_id = map_key_value(property_url, key="name", value="id")
        converter = FormatConverter(mapper=prop_name_to_id)
        converter.add_form_format(data["entries"])

    elif entry_format == "api":
        prop_id_to_name = map_key_value(property_url, key="id", value="name")
        converter = FormatConverter(mapper=prop_id_to_name)
        converter.add_api_format(data["entries"])

    converter.clean_data()
    data["entries"] = converter.get_api_format()
    data["entry_format"] = "api"

    # Send data to API
    if method == "post":
        res = requests.post(url=url, json=data, headers=headers)
        if res.status_code != 201:
            message = f"Failed to POST study related entity. {res.json()}"
            success = False
        else:
            message = "Succeded to POST study related entity"
            success = True

    elif method == "put":
        res = requests.put(url=url, json=data, headers=headers)
        if res.status_code != 200:
            message = f"Failed to PUT study related entity. {res.json()}"
            success = False
        else:
            message = "Succeded to PUT study related entity"
            success = True

    return (res.json(), message, success)




