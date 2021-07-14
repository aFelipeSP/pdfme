from typing import Any, Union
from uuid import uuid4

class PDFBase:
    """This class represents a PDF file, and deals with parsing python
    objects you add to it (with method ``add``) to PDF indirect objects.
    The python types that are parsable to their equivalent PDF types are
    ``dict`` (parsed to PDF Dictionaries), ``list``, ``tuple``, ``set``
    (parsed to PDF Arrays), ``bytes`` (no parsing is done with this type),
    ``bool`` (parsed to PDF Boolean), ``int`` (parsed to PDF Integer),
    ``float`` (parsed to PDF Real), ``str`` (parsed to PDF String) and
    ``PDFObject``, a python representation of a PDF object.

    When you are done adding objects to an instance of this class, you just
    have to call its ``output`` method to create the PDF file, and we will
    take care of creating the head, the objects, the streams, the xref
    table, the trailer, etc.

    As mentioned before, you can use python type ``bytes`` to add anything
    to the PDF file, and this can be used to add PDF objects like *Names*.

    For ``dict`` objects, the keys must be of type ``str`` and you don't
    have to use PDF Names for the keys, because they are automatically
    transformed into PDF Names when the PDF file is being created. For
    example, to add a page dict, the keys would be ``Type``, ``Content`` and
    ``Resources``, instead of ``/Type``, ``/Content`` and
    ``/Resources``, like this:

    .. code-block:: python

        base = PDFBase()
        page_dict = {
            'Type': b'/Page', 'Contents': stream_obj_ref, 'Resources': {}
        }
        base.add(page_dict)

    You can add a ``stream`` object by adding a ``dict`` like the one described
    in function :func:`pdfme.parser.parse_stream`.

    This class behaves like a ``list``, and you can get a ``PDFObject`` by
    index (you can get the index from a ``PDFObject.id`` attribute), update
    by index, iterate through the PDF PDFObjects and use ``len`` to get the
    amount of objects in this list-like class.

    Args:
        version (str, optional): Version of the PDF file. Defaults to '1.5'.
        trailer (dict, optional): You can create your own trailer dict and
            pass it as this argument.

    Raises:
        ValueError: If trailer is not dict type
    """

    def __init__(self, version: str='1.5', trailer: dict=None) -> None:
        self.version = version
        self.content = []
        if trailer is None:
            self.trailer = {}
        elif not isinstance(trailer, dict):
            raise ValueError('trailer must be a dict')
        else:
            self.trailer = trailer
        self.count = 1

    def add(
        self, py_obj: Union[
            dict, list, tuple, set, bytes, bool, int, float, str, 'PDFObject'
        ]
    ) -> 'PDFObject':
        """Add a new object to the PDF file

        Args:
            py_obj(dict, list, tuple, set, bytes, bool, int, float, str, PDFObject): Object
                to be added.

        Raises:
            TypeError: If ``py_obj`` arg is not an allowed type.

        Returns:
            PDFObject: A PDFObject representing the object added
        """

        allowed_types = (
            dict, list, tuple, set, bytes, bool, int, float, str, PDFObject
        )
        if not isinstance(py_obj, allowed_types):
            raise TypeError('object type not allowed')
        obj = PDFObject(PDFRef(self.count), py_obj)
        self.content.append(obj)
        self.count += 1
        return obj

    def __getitem__(self, i: int) -> 'PDFObject':
        if i == 0: return None
        return self.content[i - 1]

    def __setitem__(self, i: int, value: 'PDFObject') -> None:
        if i > 0:
            self.content[i - 1] = value

    def __iter__(self) -> None:
        for el in [None] + self.content:
            yield el

    def __len__(self) -> int:
        return len(self.content)

    def __str__(self) -> str:
        return str(self.content)

    def __repr__(self) -> str:
        return str(self.content)

    def _trailer_id(self) -> bytes:
        return b'<' + str(uuid4()).replace('-', '').encode('latin') + b'>'

    def output(self, buffer: Any) -> None:
        """Create the PDF file.

        Args:
            buffer (file_like): A file-like object to write the PDF file into.
        """
        header = subs('%PDF-{}\n%%\x129\x129\x129\n', self.version)
        count = len(header)
        buffer.write(header)

        xref = '\nxref\n0 {}\n0000000000 65535 f \n'.format(self.count)

        for i, obj in enumerate(self.content):
            xref += str(count).zfill(10) + ' 00000 n \n'

            obj_bytes = parse_obj(obj)
            bytes_ = subs('{} 0 obj\n', i + 1) + obj_bytes + \
                '\nendobj\n'.encode('latin')
            count += len(bytes_)
            buffer.write(bytes_)

        self.trailer['Size'] = self.count
        if 'ID' not in self.trailer:
            self.trailer['ID'] = [self._trailer_id(), self._trailer_id()]
        trailer = parse_obj(self.trailer)

        footer = '\nstartxref\n{}\n%%EOF'.format(count + 1)

        buffer.write(
            (xref + 'trailer\n').encode('latin') + trailer +
            footer.encode('latin')
        )

from .parser import PDFObject, PDFRef, parse_obj
from .utils import subs
