import json


def load_json(json_string: str) -> dict:
    """
    Load a JSON string into a Python dictionary and return the keys.

    Args:
        json_string: A string containing valid JSON data.

    Returns:
        A dictionary containing the keys of the parsed JSON object.
    """
    data = json.loads(json_string)
    return data