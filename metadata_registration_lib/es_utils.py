import json
import requests

from metadata_registration_lib.api_utils import map_key_value


def get_nb_pages(nb_hits, es_size):
    """
    Get total number of pages (returns: int) given a number of items and the page size
    """
    if nb_hits % es_size == 0:
        nb_pages = nb_hits // es_size
    else:
        nb_pages = nb_hits // es_size + 1
    return nb_pages


def get_es_index_url(es_config):
    """
    Returns a full URL of the Elastic Search index
    Parameters:
        - es_config (dict): configuration dict
    """
    if all([es_config[x] is not None for x in ["HOST", "PORT", "INDEX"]]):
        return f"{es_config['HOST']}:{es_config['PORT']}/{es_config['INDEX']}"
    else:
        raise Exception("ES server not properly configured")


def get_es_auth(es_config):
    """
    Returns an auth tuple (username, psw) if the Elastic Search server is set to "secure" else returns None
    Parameters:
        - es_config (dict): configuration dict
    """
    if es_config.get("SECURE", False):
        return (es_config["USERNAME"], es_config["PASSWORD"])
    else:
        return None


def index_study(es_index_url, es_auth, study_data, action, cv_url):
    """Index or update a study on the ES server"""
    headers = {"Content-type": "application/json"}
    study_id = study_data["id"]

    # Move "entries" and "meta_information" properties to the root
    for entry_prop, entry_value in study_data["entries"].items():
        study_data[entry_prop] = entry_value
    del study_data["entries"]

    for entry_prop, entry_value in study_data["meta_information"].items():
        study_data[entry_prop] = entry_value
    del study_data["meta_information"]

    # Replace properties CV values by expended items
    cv_items_expended = get_cv_items_expended_for_indexing(cv_url)
    study_data = expend_cv_values(study_data, cv_items_expended)

    if action == "add":
        res = requests.post(
            url=f"{es_index_url}/_create/{study_id}",
            data=json.dumps(study_data),
            headers=headers,
            auth=es_auth,
        )
    elif action == "update":
        res = requests.put(
            url=f"{es_index_url}/_doc/{study_id}",
            data=json.dumps(study_data),
            headers=headers,
            auth=es_auth,
        )

    if "error" in res.json().keys():
        raise Exception(f"Error while indexing the study: {res.json()}")

    return res.json()


def remove_study_from_index(es_index_url, es_auth, study_id):
    res = requests.delete(
        url=f"{es_index_url}/_doc/{study_id}",
        auth=es_auth,
    )
    if "error" in res.json().keys():
        raise Exception(f"Error while deleting study from index: {res.json()}")

    return res.json()


# CV related code to add labels and item synonyms to the index
def get_cv_items_expended_for_indexing(cv_url):
    cv_name_to_items = map_key_value(cv_url, key="name", value="items")

    cv_items_map = {}
    for cv_name, cv_items in cv_name_to_items.items():
        cv_items_map[cv_name] = {}
        for item in cv_items:
            expended_str = f"{item['name']} - {item['label']}"
            if len(item["synonyms"]) > 0:
                expended_str += " - " + " - ".join(item["synonyms"])
            cv_items_map[cv_name][item["name"]] = expended_str

    return cv_items_map


def expend_cv_values(study, cv_items_expended):
    for prop_name, value in study.items():
        if prop_name in cv_items_expended:
            try:
                if type(value) == list:
                    study[prop_name] = " // ".join(
                        [cv_items_expended[prop_name][v] for v in value]
                    )
                else:
                    study[prop_name] = cv_items_expended[prop_name][value]
            except:
                print(f"\tFailed to expand {value} for property {prop_name} in study")
        elif type(value) == dict:
            value = expend_cv_values(value, cv_items_expended)
        elif type(value) == list:
            for nested_value in value:
                if type(nested_value) == dict:
                    nested_value = expend_cv_values(nested_value, cv_items_expended)
                elif prop_name in cv_items_expended:
                    nested_value = cv_items_expended[prop_name][nested_value]

    return study
