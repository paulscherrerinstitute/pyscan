def convert_to_list(value):
    return [value] if (value is not None) and (not isinstance(value, list)) else value
