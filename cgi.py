def parse_header(value: str):
    parts = [p.strip() for p in value.split(';')]
    key = parts[0]
    params = {}
    for p in parts[1:]:
        if '=' in p:
            k, v = p.split('=', 1)
            params[k.strip()] = v.strip('" ')
    return key, params

class FieldStorage:
    pass