def json_str_to_yaml_str(json_str_or_object):
    """
    Convert a JSON string to a YAML string.

    Args:
    json_str (str): A string containing valid JSON.

    Returns:
    str: A string containing the equivalent YAML.
    """
    import json
    import yaml

    try:
        # Parse the JSON string to a Python object
        if isinstance(json_str_or_object, str):
            data = json.loads(json_str_or_object)
        else:
            data = json_str_or_object

        # Convert the Python object to a YAML string
        yaml_str = yaml.dump(data, sort_keys=False, allow_unicode=True)

        return yaml_str
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def json_str_to_toml_str(json_str):
    """
    Convert a JSON string to a TOML string.

    Args:
    json_str (str): A string containing valid JSON.

    Returns:
    str: A string containing the equivalent TOML.
    """
    import json
    from io import StringIO

    import toml

    try:
        # Parse the JSON string to a Python object
        data = json.loads(json_str)

        # Convert the Python object to a TOML string
        # We use StringIO to write TOML to a string instead of a file
        toml_str_io = StringIO()
        toml.dump(data, toml_str_io)
        toml_str = toml_str_io.getvalue()

        return toml_str
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"