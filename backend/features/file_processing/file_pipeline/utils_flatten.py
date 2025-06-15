def flatten_values(data):
    """
    Recursively extract all values from nested dicts and lists into a flat list.
    """
    values = []
    if isinstance(data, dict):
        for v in data.values():
            values.extend(flatten_values(v))
    elif isinstance(data, list):
        for item in data:
            values.extend(flatten_values(item))
    else:
        values.append(data)
    return values
