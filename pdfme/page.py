from typing import Iterable, Union

Number = Union[int, float]
PageType = Union[Number, str, Iterable[Number]]
MarginType = Union[int, float, Iterable[Number], dict]

class PDFPage:
    """Class that represents a PDF page, and has methods to add stream parts
    into the internal page PDF Stream Object, and other things like
    fonts, annotations and images.

    This object have ``x`` and ``y`` coordinates used by the
    :class:`pdfme.pdf.PDF` insance that contains this page. This point is called
    ``cursor`` in this class.

    Args:
        base (PDFBase): [description]
        width (Number): [description]
        height (Number): [description]
        margin_top (Number, optional): [description]. Defaults to 0.
        margin_bottom (Number, optional): [description]. Defaults to 0.
        margin_left (Number, optional): [description]. Defaults to 0.
        margin_right (Number, optional): [description]. Defaults to 0.
    """
    def __init__(
        self, base: 'PDFBase', width: Number, height: Number,
        margin_top: Number=0, margin_bottom: Number=0,
        margin_left: Number=0, margin_right: Number=0
    ):
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right

        self.width = width
        self.height = height
        self.go_to_beginning()

        self.stream = base.add({'Filter': b'/FlateDecode', '__stream__': {}})
        self.page = base.add({
            'Type': b'/Page', 'Contents': self.stream.id, 'Resources': {}
        })
        self.x_objects = {}
        self.current_id = 0

    @property
    def y(self) -> Number:
        """
        Returns:
            Number: The current vertical position of the page's cursor, from
            top (0) to bottom. This is different from ``_y`` attribute, the
            position from bottom (0) to top.
        """
        return self.height - self._y

    @y.setter
    def y(self, value):
        self._y = self.height - value

    def go_to_beginning(self) -> None:
        """Method to set the position of the cursor's page to the origin point
        of the page, considering this page margins. The origin is at the
        left-top corner of the rectangle that will contain the page's contents.
        """
        self.content_width = self.width - self.margin_right - self.margin_left
        self.content_height = self.height - self.margin_top - self.margin_bottom

        self.x = self.margin_left
        self._y = self.height - self.margin_top

    def add(self, content: Union[str, bytes]) -> int:
        """Method to add some bytes (if a string is passed, it's transformed
        into a bytes object) representing a stream portion, into this page's PDF
        internal Stream Object.

        Args:
            content (str, bytes): the stream portion to be added to this page's
                stream.

        Returns:
            int: the id of the portion added to the page's stream
        """
        if isinstance(content, str):
            content = content.encode('latin')
        current_id = self.current_id
        self.stream['__stream__'][current_id] = content
        self.current_id += 1
        return current_id

    def add_font(self, font_ref: str, font_obj_id: 'PDFRef') -> None:
        """Method to reference a PDF font in this page, that will be used inside
        this page's stream.

        Args:
            font_ref (str): the ``ref`` attribute of the
                :class:`pdfme.fonts.PDFFont` instance that will be referenced in
                this page.
            font_obj_id (PDFRef): the object id of the font being referenced
                here, already added to a :class:`pdfme.base.PDFBase` instance.
        """
        self.page['Resources'].setdefault('Font', {})
        self.page['Resources']['Font'][font_ref] = font_obj_id

    def add_annot(self, obj: dict, rect: list) -> None:
        """Method to add a PDF annotation to this page.

        The ``object`` dict should have the keys describing the annotation to
        be added. By default, this object will have the following key/values
        by default: ``Type = /Annot`` and ``Subtype = /Link``.
        You can include these keys in ``object`` if you want to overwrite any of
        the default values for them.

        Args:
            obj (dict): the annotation object.
            rect (list): a list with the following information about the
                annotation: [x, y, width, height].
        """
        if not 'Annots' in self.page:
            self.page['Annots'] = []
        _obj = {'Type': b'/Annot', 'Subtype': b'/Link'}
        _obj.update(obj)
        _obj['Rect'] = rect
        self.page['Annots'].append(_obj)

    def add_link(self, uri_id: 'PDFRef', rect: list) -> None:
        """Method to add a link annotation (a URI that opens a webpage from the
        PDF document) to this page.

        Args:
            uri_id (PDFRef): the object id of the action object created to open
                this link.
            rect (list): a list with the following information about the
                annotation: [x, y, width, height].
        """
        self.add_annot({'A': uri_id, 'H': b'/N'}, rect)

    def add_reference(self, dest: str, rect: list) -> None:
        """Method to add a reference annotation (a clickable area, that takes
        the user to a destination) to this page.

        Args:
            dest (str): the name of the dest being referenced.
            rect (list): a list with the following information about the
                annotation: [x, y, width, height].
        """
        self.add_annot({'Dest': dest}, rect)

    def add_image(
        self, image_obj_id: 'PDFRef', width: Number, height: Number
    ) -> None:
        """Method to add an image to this page.

        The position of the image will be the same as ``x`` and ``y``
        coordinates of this page.

        Args:
            image_obj_id (PDFRef): the object id of the image PDF object.
            width (int, float): the width of the image.
            height (int, float): the height of the image.
        """
        self.page['Resources'].setdefault('XObject', {})
        if not image_obj_id in self.x_objects:
            image_id = 'Im{}'.format(len(self.page['Resources']['XObject']))
            self.page['Resources']['XObject'][image_id] = image_obj_id
            self.x_objects[image_obj_id] = image_id

        self.add(
            ' q {} 0 0 {} {} {} cm /{} Do Q'.format(
                round(width, 3), round(height, 3), round(self.x, 3),
                round(self._y, 3), self.x_objects[image_obj_id]
            )
        )

from .base import PDFBase
from .parser import PDFRef