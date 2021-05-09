import re

from .encoders import encode_stream
from .utils import subs

class PDFObject:
    def __init__(self, id_=None, obj={}):
        if not isinstance(id_, PDFRef):
            raise TypeError('id_ argument must be of type PDFRef')
        self.id = id_
        self.value = obj

    def __getitem__(self, name):
        return self.value[name]

    def __setitem__(self, name, value):
        self.value[name] = value

    def __delitem__(self, name):
        del self.value[name]

    def __contains__(self, name):
        return name in self.value

class PDFRef(int):
    def __new__(cls, id_):
        return int.__new__(cls, id_)
    @property
    def ref(self):
        return subs('{} 0 R', self)

def parse_obj(obj):
    if isinstance(obj, PDFObject):
        return parse_obj(obj.value)
    elif isinstance(obj, PDFRef):
        return obj.ref
    elif isinstance(obj, dict):
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
        return str(obj).encode('latin')
    elif isinstance(obj, str):
        return ('(' + re.sub(r'([()])', r'\\\1', obj) + ')').encode('latin')
    

def parse_dict(obj):
    bytes_ = b'<<'
    for key, value in obj.items():
        bytes_ += b'/' + key.encode('latin')
        ret = parse_obj(value)
        if not ret[0] in [b'/', b'(', b'<']: bytes_ += b' '
        bytes_ += ret

    return bytes_ + b'>>'

def parse_list(obj):
    bytes_ = b'['
    for i, value in enumerate(obj):
        ret = parse_obj(value)
        if not ret[0] in [b'/', b'(', b'<'] and i != 0: bytes_ += b' '
        bytes_ += ret

    return bytes_ + b']'

def parse_stream(obj):
    stream_ = obj.pop('__stream__')
    skip_filter = obj.pop('__skip_filter__', False)

    if 'Filter' in obj and not skip_filter:
        stream = encode_stream(stream_, obj['Filter'])
    else:
        stream = stream_

    obj['Length'] = len(stream)
    ret = parse_dict(obj) + b'stream\n' + stream + b'\nendstream'
    obj['__stream__'] = stream_
    if skip_filter:
        obj['__skip_filter__'] = True
    return ret
