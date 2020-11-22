import re

from .encoders import encode_stream

def parse_obj(obj):
    if isinstance(obj, dict):
        if '__stream__' in obj:
            return parse_stream(obj)
        else:
            return parse_dict(obj)
    elif isinstance(obj, (list, tuple, set)):
        return parse_list(obj)
    elif isinstance(obj, bytes):
        return obj
    elif isinstance(obj, bool):
        return b'true' if obj else b'false'
    elif isinstance(obj, (int, float)):
        return str(obj).encode()
    elif isinstance(obj, str):
        return ('(' + re.sub(r'([()])', r'\\\1', obj) + ')').encode()
    

def parse_dict(obj):
    bytes_ = b'<<'
    for key, value in obj.items():
        bytes_ += b'/' + key.encode()
        ret = parse_obj(value)
        if not ret.startswith(b'/'): bytes_ += b' '
        bytes_ += ret

    return bytes_ + b'>>'

def parse_list(obj):
    bytes_ = b'['
    for i, value in enumerate(obj):
        ret = parse_obj(value)
        if not ret.startswith(b'/') and i != 0: bytes_ += b' '
        bytes_ += ret

    return bytes_ + b']'

def parse_stream(obj):
    stream_ = obj.pop('__stream__')

    if 'Filter' in obj:
        stream = encode_stream(stream_, obj['Filter'])
    else:
        stream = stream_

    obj['Length'] = len(stream)
    ret = parse_dict(obj) + b'stream\n' + stream + b'\nendstream'
    obj['__stream__'] = stream_
    return ret


        


    