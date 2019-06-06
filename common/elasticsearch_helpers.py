from elasticsearch import Elasticsearch
import os


def connect_to_elasticsearch(es_uri=None) -> Elasticsearch:
    if not es_uri:
        es_uri = os.getenv("ES_URI", "localhost")
    es = Elasticsearch(
        [es_uri]
    )
    return es


def flatten_data_for_es(data, prefix=""):
    """
    Transforms a JSON object into a flattened representation for generic insertion into a ES index
    Per: http://smnh.me/indexing-and-searching-arbitrary-json-data-using-elasticsearch/
    Args:
        data: Dictionary to convert
        prefix: This should start blank
    Returns: List of flattened objects to put into Elasticsearch
    """

    def flattened_data(key, type_, value):
        """
        Basic unit of flattened data for inserting into ES
        Args:
            key: dot separated list of keys
            type_: type of value
            value: actual value
        Returns: flattened data object
        """
        return {
            "key": key,
            "type": type_,
            f"value_{type_}": value
        }

    if isinstance(data, dict):
        """If data is a dict, flatten its contents"""
        accumulator = []
        for key, value in data.items():
            prefix_ = f"{prefix}." if prefix else ""
            accumulator.append(flatten_data_for_es(value, f"{prefix_}{key}"))
        return accumulator

    elif isinstance(data, list):
        """If data is a list, flatten its contents"""
        results_map = {}
        for elem in data:
            flattened = flatten_data_for_es(elem)
            for result in flattened:
                key = result["key"]
                if key not in results_map:
                    results_map[key] = {}
                type_ = result["type"]
                if type_ not in results_map[key]:
                    results_map[key][type_] = []

                to_append = result[f"value_{type_}"]
                if not isinstance(to_append, list):
                    to_append = [to_append]

                results_map[key][type_].extend(to_append)

        """Base case - build results list"""
        result = []
        for key, value in results_map.items():
            for type_ in value:
                result.append(flattened_data(key, type_, results_map[key][type_]))

        return result

    elif isinstance(data, str):
        result = flattened_data(prefix, 'string', data)

    elif isinstance(data, int):
        result = flattened_data(prefix, 'long', data)

    elif isinstance(data, float):
        result = flattened_data(prefix, 'float', data)

    elif isinstance(data, bool):
        result = flattened_data(prefix, 'boolean', data)

    elif data is None:
        result = flattened_data(prefix, 'null', data)

    else:
        raise ValueError("Object is not JSON serializable.")

    return [result] if result else []
