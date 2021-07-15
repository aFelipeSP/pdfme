import re
from typing import Iterable, Union
class PDFObject:
    """A class that represents a PDF object.

    This object has a :class:`pdfme.parser.PDFRef` ``id`` attribute representing
    the id of this object inside the PDF document, and acts as a dict, so the
    user can update any property of this PDF object like you would do with a
    dict.

    Args:
        id_ (PDFRef): The id of this object inside the PDF document.
        obj (dict, optional): the dict representing the PDF object.
    """
    def __init__(self, id_: 'PDFRef', obj: dict=None) -> None:
        if not isinstance(id_, PDFRef):
            raise TypeError('id_ argument must be of type PDFRef')
        self.id = id_
        self.value = {} if obj is None else obj

    def __getitem__(self, name):
        return self.value[name]

    def __setitem__(self, name, value):
        self.value[name] = value

    def __delitem__(self, name):
        del self.value[name]

    def __contains__(self, name):
        return name in self.value

class PDFRef(int):
    """An ``int`` representing the id of a PDF object.

    This is a regular ``int`` that has an additional property called ``ref``
    with a representation of this object, to be referenced elsewhere in the PDF
    document.
    """
    def __new__(cls, id_):
        return int.__new__(cls, id_)
    @property
    def ref(self) -> bytes:
        """
        Returns:
            bytes: bytes with a representation of this object, to be referenced
            elsewhere in the PDF document.
        """
        return subs('{} 0 R', self)

ObjectType = Union[
    PDFObject, PDFRef, dict, list, tuple, set, bytes, bool, int, float, str
]

def parse_obj(obj: ObjectType) -> bytes:
    """Function to convert a python object to a bytes object representing the
    corresponding PDF object.

    Args:
        obj (PDFObject, PDFRef, dict, list, tuple, set, bytes, bool, int, float,
            str): the object to be converted to a PDF object.

    Returns:
        bytes: bytes representing the corresponding PDF object.
    """
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


def parse_dict(obj: dict) -> bytes:
    """Function to convert a python dict to a bytes object representing the
    corresponding PDF Dictionary.

    Args:
        obj (dict): the dict to be converted to a PDF Dictionary.

    Returns:
        bytes: bytes representing the corresponding PDF Dictionary.
    """
    bytes_ = b'<<'
    for key, value in obj.items():
        bytes_ += b'/' + key.encode('latin')
        ret = parse_obj(value)
        if not ret[0] in [b'/', b'(', b'<']: bytes_ += b' '
        bytes_ += ret

    return bytes_ + b'>>'

def parse_list(obj: Iterable) -> bytes:
    """Function to convert a python iterable to a bytes object representing the
    corresponding PDF Array.

    Args:
        obj (iterable): the iterable to be converted to a PDF Array.

    Returns:
        bytes: bytes representing the corresponding PDF Array.
    """
    bytes_ = b'['
    for i, value in enumerate(obj):
        ret = parse_obj(value)
        if not ret[0] in [b'/', b'(', b'<'] and i != 0: bytes_ += b' '
        bytes_ += ret

    return bytes_ + b']'

def parse_stream(obj: dict) -> bytes:
    """Function to convert a dict representing a PDF Stream object to a bytes
    object.

    A dict representing a PDF stream should have a ``'__stream__`` key
    containing the stream bytes. You don't have to include ``Length`` key in the
    dict, as it is calculated by us. The value of ``'__stream__'`` key must
    be of type ``bytes`` or a dict whose values are of type ``bytes``.
    If you include a ``Filter`` key, a encoding is automatically done in the
    stream (see :meth:`pdfme.encoders.encode_stream` function for
    supported encoders). If the contents of the stream are already encoded
    using the filter in ``Filter`` key, you can skip the encoding process
    by including the ``__skip_filter__`` key.

    Args:
        obj (dict): the dict representing a PDF stream.

    Returns:
        bytes: bytes representing the corresponding PDF Stream.
    """
    stream_ = obj.pop('__stream__')
    skip_filter = obj.pop('__skip_filter__', False)

    if isinstance(stream_, bytes):
        stream_str = stream_
    elif isinstance(stream_, dict):
        stream_str = b''.join(stream_.values())
    else:
        raise Exception(
            'streams must be bytes or a dict of bytes: ' + str(stream_)
        )

    stream = encode_stream(stream_str, obj['Filter']) \
        if 'Filter' in obj and not skip_filter else stream_str

    obj['Length'] = len(stream)
    ret = parse_dict(obj) + b'stream\n' + stream + b'\nendstream'
    obj['__stream__'] = stream_
    if skip_filter:
        obj['__skip_filter__'] = True
    return ret

from .encoders import encode_stream
from .utils import subs
