import json
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Union

Number = Union[int, float]
PageType = Union[Number, str, Iterable[Number]]
MarginType = Union[int, float, Iterable[Number], dict]
ColorType = Union[int, float, str, list, tuple]
ImageType = Union[str, Path, BytesIO]
TextType = Union[str, list, tuple, dict]
class PDF:
    """Class that represents a PDF document, and has methods to add pages,
    and to add paragraphs, images, tables and a mix of this, a content box,
    to them.

    You can use this class to create a PDF file, by adding one page at a
    time, and adding stuff to each page you add, like this:

    .. code-block:: python

        from pdfme import PDF

        pdf = PDF()
        pdf.add_page()
        pdf.text('This is a paragraph')

        with open('document.pdf', 'wb') as f:
            pdf.output(f)

    Through the constructor arguments you can modify the default features
    of the PDF document, like the size of the pages, their orientation,
    the page numbering options, and the appearance of the text. These are
    used everytime you create a new page, or a new paragraph, but you
    can overwrite these for each case.

    You can change the default values for the pages by calling
    :meth:`pdfme.pdf.PDF.setup_page`, and change the default values for text
    by changing attributes ``font_family``, ``font_size``, ``font_color``,
    ``text_align`` and ``line_height``.

    Methods :meth:`pdfme.pdf.PDF.text`, :meth:`pdfme.pdf.PDF.image`,
    :meth:`pdfme.pdf.PDF.table` and :meth:`pdfme.pdf.PDF.content` are the main
    functions to add paragraphs, images, tables and content boxes respectively,
    and all of them, except the image method, take into account the margins of
    the current page you are working on, and create new pages automatically if
    the stuff you are adding needs more than one page. If you want to be
    specific about the position and the size of the paragraphs, tables and
    content boxes you are inserting, you can use methods
    :meth:`pdfme.pdf.PDF._text`, :meth:`pdfme.pdf.PDF._table` and
    :meth:`pdfme.pdf.PDF._content` instead, but these don't handle the creation
    of new pages like the first ones.

    Each page has attributes ``x`` and ``y`` that are used to place elements
    inside them, and for the methods that receive ``x`` and ``y`` arguments,
    if they are None, the page's ``x`` and ``y`` attributes are used instead.

    For more information about paragraphs see :class:`pdfme.text.PDFText`, and
    about tables :class:`pdfme.table.PDFTable`.

    Although you can add all of the elements explained so far, we recommend
    using content boxes only, because all of the additional funcionalities they
    have, including its ability to embed other elements. For more information
    about content boxes see :class:`pdfme.content.PDFContent`.

    Paragraphs, tables and content boxes use styles to give format to the
    content inside of them, and sometimes styling can get repetitive. This is
    why there's a dict attribute called ``formats`` where you can add named
    style dicts and used them everywhere inside this document, like this:


    .. code-block:: python

        from pdfme import PDF

        pdf = PDF()
        pdf.formats['link'] = {
            'c': 'blue',
            'u': True
        }
        pdf.add_page()
        pdf.text({
            '.': 'this is a link',
            'style': 'link',
            'uri': 'https://some.domain.com'
        })

    If you find yourself using a piece of text often in the document, you can
    add it to the dict attribute ``context`` and include it in any paragraph in
    the document by using its key in the dict, like this:

    .. code-block:: python

        from pdfme import PDF

        pdf = PDF()
        pdf.context['arln'] = 'A Really Long Name'
        pdf.add_page()
        pdf.text({
            '.': ['The following name is ', {'var': 'arln'}, '.']
        })

    There are some special ``context`` variables that are used by us that start
    with symbol ``$``, so it's adviced to name your own variables without this
    symbol in the beginning. The only of these variables you should care about
    is ``$page`` that contains the number of the current page.

    You can add as much running sections as you want by using
    :meth:`pdfme.pdf.PDF.add_running_section`. Running sections are
    content boxes that are included on every page you create after adding them.
    Through these you can add a header and a footer to the PDF.

    If you want a simpler and more powerful interface, you should use
    :class:`pdfme.document.PDFDocument`.

    Args:
        page_size (str, int, float, tuple, list, optional): this argument sets
            the dimensions of the page. See :func:`pdfme.utils.get_page_size`.
        rotate_page (bool, optional): whether the page dimensions should be
            inverted (True), or not (False).
        margin (str, int, float, tuple, list, dict, optional): the margins of
            the pages. See :func:`pdfme.utils.parse_margin`.
        page_numbering_offset (int, float, optional): if the number of the page
            is included, this argument will set the offset of the page. For
            example if the current page is the 4th one, and the offset is 3, the
            page number displayed in the current page will be 1.
        page_numbering_style (str, optional): the style of the page number.
            Options are ``arabic`` (1,2,3,...) and ``roman`` (I, II, III, IV,
            ...).
        font_family (str, optional): The name of the font family. Options are
            ``Helvetica`` (default), ``Times``, ``Courier``, ``Symbol`` and
            ``ZapfDingbats``. You will also be able to add new fonts in a future
            release.
        font_size (in, optional): The size of the font.
        font_color (int, float, str, list, tuple, optional): The color of the
            font. See :func:`pdfme.color.parse_color`.
        text_align (str, optional):  ``'l'`` for left (default), ``'c'`` for
            center, ``'r'`` for right and ``'j'`` for justified text.
        line_height (int, float, optional): space between the lines of the
            paragraph. See :class:`pdfme.text.PDFText`.
        indent (int, float, optional): space between left of the paragraph, and
            the beggining of the first line. See :class:`pdfme.text.PDFText`.
        outlines_level (int, optional): the level of the outlines to be
            displayed on the outlines panel when the PDF document is opened.
    """
    def __init__(
        self, page_size: PageType='a4', rotate_page: bool=False,
        margin: MarginType=56.693, page_numbering_offset: Number=0,
        page_numbering_style: str='arabic', font_family: str='Helvetica',
        font_size: Number=11, font_color: ColorType=0.1, text_align: str='l',
        line_height: Number=1.1, indent: Number=0, outlines_level: int=1
    ) -> None:
        self.setup_page(page_size, rotate_page, margin)
        self.page_numbering_offset = page_numbering_offset
        self.page_numbering_style = page_numbering_style

        self.font_family = font_family
        self.font_size = font_size
        self.font_color = font_color
        self.text_align = text_align
        self.line_height = line_height
        self.indent = indent
        self.outlines_level = outlines_level

        self.formats = {}
        self.context = {}

        self.dests = {}
        self.uris = {}
        self.pages = []
        self.running_sections = []
        self.outlines = []

        self.base = PDFBase()
        self.root = self.base.add({ 'Type': b'/Catalog'})
        self.base.trailer['Root'] = self.root.id

        self.fonts = PDFFonts()
        self.used_fonts = {}
        self.images = {}
        self._add_or_get_font('Helvetica', 'n')

    @property
    def page(self) -> 'PDFPage':
        """
        Returns:
            PDFPage: current page
        """
        return self.pages[self._page_index]

    @property
    def page_index(self) -> int:
        """
        Returns:
            int: current page index.
        """
        return self._page_index

    @page_index.setter
    def page_index(self, page_index):
        self._page_index = page_index
        self.context['$page'] = self.get_page_number()

    @property
    def width(self) -> float:
        """
        Returns:
            float: current page width
        """
        return self.page.width

    @property
    def height(self) -> float:
        """
        Returns:
            float: current page height
        """
        return self.page.height

    def setup_page(
        self, page_size: PageType=None, rotate_page: bool=None,
        margin: MarginType=None
    ) -> None:
        """Method to set the page features defaults. These values will be used
        from now on when adding new pages.

        Args:
            page_size (str, int, float, tuple, list, optional): this argument
                sets the dimensions of the page.
                See :func:`pdfme.utils.get_page_size`.
            rotate_page (bool, optional): whether the page dimensions should be
                inverted (True), or not (False).
            margin (str, int, float, tuple, list, dict, optional): the margins
                of the pages. See :func:`pdfme.utils.parse_margin`.
        """
        if page_size is not None:
            self.page_width, self.page_height = get_page_size(page_size)
        if rotate_page is not None:
            self.rotate_page = rotate_page
        if margin is not None:
            self.margin = parse_margin(margin)

    def add_page(
        self, page_size: PageType=None, rotate_page: bool=None,
        margin: MarginType=None
    ) -> None:
        """Method to add a new page. If provided, arguments will only apply for
        the page being added.

        Args:
            page_size (str, int, float, tuple, list, optional): this argument
                sets the dimensions of the page.
                See :func:`pdfme.utils.get_page_size`.
            rotate_page (bool, optional): whether the page dimensions should be
                inverted (True), or not (False).
            margin (str, int, float, tuple, list, dict, optional): the margins
                of the page. See :func:`pdfme.utils.parse_margin`.
        """
        if page_size is not None:
            page_width, page_height = get_page_size(page_size)
        else:
            page_height, page_width = self.page_height, self.page_width

        if (rotate_page is None and self.rotate_page) or rotate_page:
            page_height, page_width = page_width, page_height

        margin_ = copy(self.margin)
        if margin is not None:
            margin_.update(parse_margin(margin))

        page = PDFPage(self.base, page_width, page_height,
            **{'margin_' + side: value for side, value in margin_.items()}
        )

        self.pages.append(page)
        self.page_index = len(self.pages) - 1

        for running_section in self.running_sections:
            self._content(**running_section)

        page.go_to_beginning()

    def add_running_section(
        self, content: dict, width: Number, height: Number, x: Number, y:Number
    ) -> None:
        """Method to add running sections, like a header and a footer, to this
        document.

        Running sections are content boxes that are included on every page you
        create after adding them.

        Args:
            content (dict): a content dict like the one you pass to create a
                instance of :class:`pdfme.content.PDFContent`.
            width (int, float, optional): The width of the rectangle where the
                contents will be arranged.
            height (int, float, optional): The height of the rectangle where the
                contents will be arranged.
            x (int, float, optional): The x position of the left of the
                rectangle.
            y (int, float, optional): The y position of the top of the
                rectangle.
        """
        self.running_sections.append(dict(
            content=content, width=width, height=height, x=x, y=y
        ))

    def add_font(
        self, fontfile: str, font_family: str, mode: str='n'
    ) -> None:
        """Method to add a new font to this document. This functionality is not
        ready yet.

        Args:
            fontfile (str): the path of the fontfile.
            font_family (str): the name of the font family being added.
            mode (str, optional): the mode of the font being added. It can be
                ``n`` for normal, ``b`` for bold and ``i`` for italics
                (oblique).
        """
        self.fonts.load_font(fontfile, font_family, mode)

    def _add_or_get_font(self, font_family: str, mode: str) -> tuple:
        """Method to add a new font to the already used fonts list, if it has
        not been added, that returns information about the font to be used in
        other places in the PDF.

        Args:
            font_family (str): the name of the font family being used.
            mode (str, optional): the mode of the font being used. It can be
                ``n`` for normal, ``b`` for bold and ``i`` for italics
                (oblique).

        Returns:
            tuple: tuple with first element as the name of the font (a name used
            in the PDF text streams), and the second as the id of the inner
            PDF object that represents the font.
        """
        f = (font_family, mode)
        if f in self.used_fonts:
            return self.used_fonts[f]
        font = self.fonts.get_font(*f)
        font_obj = font.add_font(self.base)
        self.used_fonts[(font_family, mode)] = (font.ref, font_obj.id)
        return font.ref, font_obj.id

    def _used_font(self, font_family: str, mode: str) -> None:
        """Method to add a font to the current page.

        Args:
            font_family (str): the name of the font family being used.
            mode (str, optional): the mode of the font being used. It can be
                ``n`` for normal, ``b`` for bold and ``i`` for italics
                (oblique).
        """
        f = (font_family, mode)
        font_args = self._add_or_get_font(*f)
        self.page.add_font(*font_args)

    def create_image(
        self, image: ImageType, extension: str=None, image_name: str=None
    ) -> 'PDFImage':
        """Method to create a PDF image.

        Arguments for this method are the same as :class:`pdfme.image.PDFImage`.

        Returns:
            PDFImage: object representing the PDF image.
        """
        return PDFImage(image, extension, image_name)

    def add_image(
        self, pdf_image: 'PDFImage', x: Number=None, y: Number=None,
        width: Number=None, height:Number=None, move: str='bottom'
    ) -> None:
        """Method to add a PDF image to the current page.

        Args:
            pdf_image (PDFImage): the PDF image.
            x (int, float, optional): The x position of the left of the
                image.
            y (int, float, optional): The y position of the top of the
                image.
            width (int, float, optional): The width of the image. If this and
                ``height`` are None, the width will be the same as the page
                content width, but if this is None and ``height`` is not, the
                width will be calculated from ``height``, keeping the proportion
                of the image.
            height (int, float, optional): The height of the image. If this is
                None, the height will be calculated from the image ``width``,
                keeping the proportion.
            move (str, optional): wheter it should move page x coordinate to
                the right side of the image (``next``) or if it should move
                page y coordinate to the bottom of the image (``bottom``)
                (default).
        """
        if pdf_image.image_name not in self.images:
            image_obj = self.base.add(pdf_image.pdf_obj)
            self.images[pdf_image.image_name] = image_obj.id
        else:
            image_obj = self.base[self.images[pdf_image.image_name]]

        h = pdf_image.height
        w = pdf_image.width

        if width is None and height is None:
            width = self.page.content_width
            height = width * h/w
        elif width is None:
            width = height * w/h
        elif height is None:
            height = width * h/w

        if x is not None:
            self.page.x = x
        if y is not None:
            self.page._y = y

        self.page.add_image(image_obj.id, width, height)

        if move == 'bottom':
            self.page.y += height
        if move == 'next':
            self.page.x += width

    def image(
        self, image: ImageType, extension: str=None, image_name: str=None,
        x: Number=None, y: Number=None, width: Number=None, height:Number=None,
        move: str='bottom'
    ) -> None:
        """Method to create and add a PDF image to the current page.

        Args:
            image (str, Path, BytesIO): see :class:`pdfme.image.PDFImage`.
            extension (str, optional): see :class:`pdfme.image.PDFImage`.
            image_name (str, optional): see :class:`pdfme.image.PDFImage`.
            x (int, float, optional): the x position of the left of the
                image.
            y (int, float, optional): the y position of the top of the
                image.
            width (int, float, optional): the width of the image. If this and
                ``height`` are None, the width will be the same as the page
                content width, but if this is None and ``height`` is not, the
                width will be calculated from ``height``, keeping the proportion
                of the image.
            height (int, float, optional): the height of the image. If this is
                None, the height will be calculated from the image ``width``,
                keeping the proportion.
            move (str, optional): wheter it should move page x coordinate to
                the right side of the image (``next``) or if it should move
                page y coordinate to the bottom of the image (``bottom``)
                (default).
        """
        pdf_image = self.create_image(image, extension, image_name)
        self.add_image(
            pdf_image, x=x, y=y, width=width, height=height, move=move
        )

    def _default_paragraph_style(
        self, width: Number=None, height:Number=None, text_align: str=None,
        line_height: Number=None, indent: Number=None
    ) -> dict:
        """This method returns a dict with each of the arguments as the keys.
        If they are None, the PDF default value for each of them is used.

        For more information about the arguments of this method see
        :class:`pdfme.text.PDFText`

        Args:
            width (Number, optional): the width of the paragraph.
            height (Number, optional): the height of the paragraph.
            text_align (str, optional): the text align of the paragraph.
            line_height (Number, optional): the line height of the paragraph.
            indent (Number, optional): the indent of the paragraph.

        Returns:
            dict: dict with the default and the given parameters combined.
        """
        return dict(
            width = self.page.width - self.page.margin_right - self.page.x \
                if width is None else width,
            height = self.page.height - self.page.margin_bottom - self.page.y \
                if height is None else height,
            text_align = self.text_align if text_align is None else text_align,
            line_height = self.line_height if line_height is None \
                else line_height,
            indent = self.indent if indent is None else indent,
        )

    def _init_text(self, content: TextType) -> dict:
        """Method that prepares the paragraph passed as argument to be used in
        other methods.

        Args:
            content (str, list, tuple, dict): the paragraph object.

        Returns:
            dict: dict with the prepared paragraph.
        """
        style = {
            'f': self.font_family, 's': self.font_size, 'c': self.font_color
        }
        if isinstance(content, str):
            content = {'style': style, '.': [content]}
        elif isinstance(content, (list, tuple)):
            content = {'style': style, '.': content}
        elif isinstance(content, dict):
            style_str = [k[1:] for k in content.keys() if k.startswith('.')]
            if len(style_str) > 0:
                style.update(parse_style_str(style_str[0], self.fonts))
            style.update(process_style(content.get('style'), self))
            content['style'] = style
        return content

    def _position_and_size(
        self, x: Number=None, y: Number=None, width: Number=None,
        height: Number=None
    ) -> tuple:
        """Method that returns a tuple with the arguments passed, with default
        values if they are None.

        Args:
            x (int, float, optional): The x position of the left of the
                element.
            y (int, float, optional): The y position of the top of the
                element.
            width (int, float, optional): The width of the element.
            height (int, float, optional): The height of the element.

        Returns:
            tuple: tuple with the new ``x``,  ``y``, ``width`` and ``height``.
        """
        if x is not None:
            self.page.x = x
        if y is not None:
            self.page.y = y
        if width is None:
            width = self.page.width - self.page.margin_right - self.page.x
        if height is None:
            height = self.page.height - self.page.margin_bottom - self.page.y
        return self.page.x, self.page._y, width, height

    def get_page_number(self) -> str:
        """Method that returns the string reprensentation of the number of the
        current page.

        Returns:
            str: string with the page number that depends on attributes
            ``page_numbering_offset`` and ``page_numbering_style``.
        """
        page = self.page_index + 1 + self.page_numbering_offset
        return to_roman(page) if self.page_numbering_style == 'roman'\
            else str(page)

    def _create_text(
        self, content: TextType, width: Number=None, height: Number=None,
        text_align: str=None, line_height: Number=1.1, indent: Number=0,
        list_text: str=None, list_indent: Number=None, list_style: dict=None
    ) -> 'PDFText':
        """Method to create a paragraph.

        For more information about the arguments see
        :class:`pdfme.text.PDFText`.

        Returns:
            PDFText: object that represents a paragraph.
        """
        par_style = self._default_paragraph_style(
            width, height, text_align, line_height, indent
        )
        par_style.update({
            'list_text': list_text, 'list_indent': list_indent,
            'list_style': list_style
        })
        content = self._init_text(content)
        pdf_text = PDFText(content, fonts=self.fonts, pdf=self, **par_style)
        return pdf_text

    def _add_text(
        self, text_stream: str, x: Number=None, y: Number=None,
        width: Number=None, height: Number=None, graphics_stream: str=None,
        used_fonts: tuple=None, ids: dict=None, move: str='bottom'
    ) -> None:
        """Method to add a paragraph to the current page. The arguments for this
        method are obtained from the attribute ``result`` of class
        :class:`pdfme.text.PDFText`.

        For information about the arguments of this method see
        :meth:`pdfme.text.PDFTextBase.result`
        """
        stream = get_paragraph_stream(x, y, text_stream, graphics_stream)
        self.page.add(stream)

        for font in used_fonts:
            self._used_font(*font)

        for id_, rects in ids.items():
            if len(rects) == 0:
                continue
            if id_.startswith('$label:'):
                d = rects[0]
                x_ref = x + d[0]
                self.dests[id_[7:]] = [
                    self.page.page.id, b'/XYZ', round(x_ref, 3),
                    round(y + d[3], 3), round(x_ref/self.page.width, 3) + 1
                ]
            elif id_.startswith('$ref:'):
                for r in rects:
                    self.page.add_reference(
                        id_[5:],
                        [
                            round(x + r[0], 3), round(y + r[1], 3),
                            round(x + r[2], 3), round(y + r[3], 3)
                        ]
                    )
            elif id_.startswith('$uri:'):
                link = id_[5:]
                if not link in self.uris:
                    uri = self.base.add(
                        {'Type': b'/Action', 'S': b'/URI', 'URI': link}
                    )
                    self.uris[link] = uri.id

                for r in rects:
                    self.page.add_link(
                        self.uris[link],
                        [
                            round(x + r[0], 3), round(y + r[1], 3),
                            round(x + r[2], 3), round(y + r[3], 3)
                        ]
                    )
            elif id_.startswith('$outline:'):
                outline_data = json.loads(id_[9:])
                outline = self.outlines
                for _ in range(outline_data['level'] - 1):
                    outline = outline[-1].setdefault('children', [])

                outline.append(outline_data)

        if move == 'bottom':
            self.page.y += height
        if move == 'next':
            self.page.x += width

    def _text(
        self, content: Union[TextType, 'PDFText'], width: Number=None,
        height: Number=None, x: Number=None, y: Number=None,
        text_align: str=None, line_height: Number=1.1, indent: Number=0,
        list_text: str=None, list_indent: Number=None, list_style: dict=None,
        move: str='bottom'
    ) -> 'PDFText':
        """Method to create and add a paragraph to the current page.

        If ``content`` is a PDFText, the method ``run`` for this instance will
        be called with the new rectangle passed to this function.
        Else, this method will try to build a new PDFText instance with argument
        ``content`` and call method ``run`` afterwards.

        For more information about the arguments see
        :class:`pdfme.text.PDFText`.

        Returns:
            PDFText: object that represents the paragraph.
        """
        x, y, width, height = self._position_and_size(x, y, width, height)
        if isinstance(content, PDFText):
            pdf_text = content
            pdf_text.run(x, y, width, height)
        else:
            pdf_text = self._create_text(
                content, width, height, text_align, line_height, indent,
                list_text, list_indent, list_style
            )
            pdf_text.run(x, y)

        self._add_text(move=move, **pdf_text.result)
        return pdf_text

    def text(
        self, content: TextType, text_align: str=None, line_height: Number=1.1,
        indent: Number=0, list_text: str=None, list_indent: Number=None,
        list_style: dict=None
    ) -> None:
        """Method to create and add a paragraph to this document. This method
        will keep adding pages to the PDF until all the contents of the
        paragraph are added to the document.

        For more information about the arguments see
        :class:`pdfme.text.PDFText`.
        """
        pdf_text = self._text(
            content, x=self.page.margin_left, width=self.page.content_width,
            text_align=text_align, line_height=line_height, indent=indent,
            list_text=list_text, list_indent=list_indent, list_style=list_style
        )
        while not pdf_text.finished:
            self.add_page()
            pdf_text = self._text(pdf_text, self.page.content_width,
                self.page.content_height, self.page.margin_left,
                self.page.margin_top
            )

    def _default_content_style(self) -> dict:
        """This method returns a dict with the PDF default values used by
        content boxes.

        For more information about the keys in the dict returned by this method
        see :class:`pdfme.text.PDFText`

        Returns:
            dict: dict with the default values.
        """
        return dict(
            f=self.font_family, s=self.font_size, c=self.font_color,
            text_align=self.text_align, line_height=self.line_height,
            indent=self.indent
        )

    def _create_table(
        self, content: Iterable, width: Number=None, height: Number=None,
        x: Number=None, y: Number=None, widths: Iterable=None,
        style: Union[dict, str]=None, borders: Iterable=None,
        fills: Iterable=None
    ) -> 'PDFTable':
        """Method to create a table.

        For more information about this method arguments see
        :class:`pdfme.table.PDFTable`.

        Returns:
            PDFTable: object that represents a table.
        """
        style_ = self._default_content_style()
        style_.update(process_style(style, self))
        pdf_table = PDFTable(
            content, self.fonts, x, y, width, height,
            widths, style_, borders, fills, self
        )
        return pdf_table

    def _table(
        self, content: Union[Iterable, 'PDFTable'], width: Number=None,
        height: Number=None, x: Number=None, y: Number=None,
        widths: Iterable=None, style: Union[dict, str]=None,
        borders: Iterable=None, fills: Iterable=None, move: str='bottom'
    ) -> 'PDFTable':
        """Method to create and add a table to the current page.

        If ``content`` is a PDFTable, the method ``run`` for this instance will
        be called with the new rectangle passed to this function.
        Else, this method will try to build a new PDFTable instance with
        argument ``content`` and call method ``run`` afterwards.

        For more information about this method arguments see
        :class:`pdfme.table.PDFTable`.

        Returns:
            PDFTable: object that represents a table.
        """

        x, y, width, height = self._position_and_size(x, y, width, height)

        if isinstance(content, PDFTable):
            pdf_table = content
            pdf_table.run(x, y, width, height)
        else:
            pdf_table = self._create_table(
                content, width, height, x, y, widths, style, borders, fills
            )
            pdf_table.run()

        self._add_graphics([*pdf_table.fills, *pdf_table.lines])
        self._add_parts(pdf_table.parts)

        if move == 'bottom':
            self.page.y += pdf_table.current_height
        if move == 'next':
            self.page.x += width

        return pdf_table

    def table(
        self, content: Iterable, widths: Iterable=None,
        style: Union[str, dict]=None, borders: Iterable=None,
        fills: Iterable=None
    ) -> None:
        """Method to create and add a table to this document. This method
        will keep adding pages to the PDF until all the contents of the
        table are added to the document.

        For more information about this method arguments see
        :class:`pdfme.table.PDFTable`.
        """
        pdf_table = self._table(
            content, widths=widths, style=style, borders=borders, fills=fills,
            x=self.page.margin_left, width=self.page.content_width
        )
        while not pdf_table.finished:
            self.add_page()
            pdf_table = self._table(
                pdf_table, self.page.content_width, self.page.content_height,
                self.page.margin_left, self.page.margin_top
            )

    def _create_content(
        self, content: dict, width: Number=None, height: Number=None,
        x: Number=None, y: Number=None
    ) -> 'PDFContent':
        """Method to create a content box.

        For more information about this method arguments see
        :class:`pdfme.content.PDFContent`.

        Returns:
            PDFContent: object that represents a content box.
        """
        style = self._default_content_style()
        content = content.copy()
        style.update(process_style(content.get('style'), self))
        content['style'] = style
        pdf_content = PDFContent(content, self.fonts, x, y, width, height, self)
        return pdf_content

    def _content(
        self, content: Union[dict, 'PDFContent'], width: Number=None,
        height: Number=None, x: Number=None, y: Number=None, move: str='bottom'
    ) -> 'PDFContent':
        """Method to create and add a content box to teh current page.

        If ``content`` is a PDFContent, the method ``run`` for this instance
        will be called with the new rectangle passed to this function.
        Else, this method will try to build a new PDFContent instance with
        argument ``content`` and call method ``run`` afterwards.

        For more information about this method arguments see
        :class:`pdfme.content.PDFContent`.

        Returns:
            PDFContent: object that represents a content box.
        """
        x, y, width, height = self._position_and_size(x, y, width, height)

        if isinstance(content, PDFContent):
            pdf_content = content
            pdf_content.run(x, y, width, height)
        else:
            pdf_content = self._create_content(content, width, height, x, y)
            pdf_content.run()

        self._add_graphics([*pdf_content.fills,*pdf_content.lines])
        self._add_parts(pdf_content.parts)

        if move == 'bottom':
            self.page.y += pdf_content.current_height
        if move == 'next':
            self.page.x += width

        return pdf_content

    def content(self, content: dict) -> None:
        """Method to create and add a content box to this document. This method
        will keep adding pages to the PDF until all the contents are added to
        the document.

        Args:
            content (dict): see :class:`pdfme.content.PDFContent`.
        """
        pdf_content = self._content(
            content, x=self.page.margin_left, width=self.page.content_width
        )
        while not pdf_content.finished:
            self.add_page()
            pdf_content = self._content(pdf_content,
                self.page.content_width, self.page.content_height,
                self.page.margin_left, self.page.margin_top
            )

    def _add_graphics(self, graphics: Iterable) -> None:
        """Method to add a list of PDF graphics streams to current page.

        Args:
            graphics (list, tuple): an iterable with strings of PDF graphics
                streams.
        """
        stream = create_graphics(graphics)
        self.page.add(stream)

    def _add_parts(self, parts: Iterable) -> None:
        """Method to add a list of parts to current page.

        Each element of ``parts`` should be a dictionary with a ``type`` key,
        with value ``'text'`` for paragraph streams, or ``'image'``
        for images. The other keys in a ``text`` part are the ones obtained from
        PDFText ``result`` property, and the other keys in a ``image`` part,
        should be the same as the arguments for :meth:`pdfme.pdf.PDF.add_image`
        method.

        Args:
            parts (list, tuple): the iterable just explained.
        """
        for part in parts:
            part = part.copy()
            type_ = part.pop('type')
            if type_ == 'paragraph':
                self._add_text(**part)
            elif type_ == 'image':
                self.add_image(**part)

    def _build_pages_tree(self, page_list:list, first_level:bool=True) -> None:
        """Method to build the PDF pages tree.

        Args:
            page_list (list): a list of PDF page objects or PDFPage objects to
                be added to the PDF pages tree.
            first_level (bool, optional): whether you are calling this method
                from outside (True) or recursively from inside (False).
        """
        new_page_list = []
        count = 0
        for page in page_list:
            if first_level:
                page_size = [page.width, page.height]
                page = page.page
                page['MediaBox'] = [0, 0] + page_size

            if count % 6 == 0:
                new_page_list.append(
                    self.base.add({'Type': b'/Pages', 'Kids': [], 'Count': 0})
                )
                count += 1

            last_parent = new_page_list[-1]
            page['Parent'] = last_parent.id
            last_parent['Kids'].append(page.id)
            last_parent['Count'] += 1

        if count == 1:
            self.root['Pages'] = new_page_list[0].id
        else:
            self._build_pages_tree(new_page_list, False)

    def _build_dests_tree(
        self, keys: list, vals: list, first_level: bool=True
    ) -> None:
        """Method to build the PDF dests tree.

        Args:
            keys (list): a list of the keys of the dests to be added to the
                PDF dests tree.
            values (list): a list of the corresponding values for each key in
                ``keys`` list.
            first_level (bool, optional): whether you are calling this method
                from outside (True) or recursively from inside (False).
        """
        k = 7
        new_keys = []
        new_vals = []
        i = 0
        length = len(keys)
        obj = None
        count = 0

        while i < length:
            key = keys[i]
            val = vals[i]
            if i % k == 0:
                count += 1
                obj = self.base.add({})
                obj['Limits'] = [key if first_level else val[0], None]
                if first_level: obj['Names'] = []
                else: obj['Kids'] = []

            if first_level:
                obj['Names'].append(key)
                obj['Names'].append(val)
            else:
                obj['Kids'].append(key)

            if (i + 1) % k == 0 or (i + 1) == length:
                obj['Limits'][1] = key if first_level else val[1]
                new_keys.append(obj.id)
                new_vals.append(obj['Limits'])

            i += 1

        if count == 1:
            del obj['Limits']
            if not 'Names' in self.root: self.root['Names'] = {}
            self.root['Names']['Dests'] = obj.id
        else:
            self._build_dests_tree(new_keys, new_vals, False)

    def _build_dests(self) -> None:
        """Method to create and add the dests tree to the document.
        """
        dests = list(self.dests.keys())
        if len(dests) == 0:
            return
        dests.sort()
        self._build_dests_tree(dests, [self.dests[k] for k in dests])

    def _build_outlines_tree(
        self, outlines: list, parent: 'PDFObject', level: int
    ) -> None:
        """Method to build a PDF outline tree.

        Args:
            outlines (list): list of outlines.
            parent (PDFObject): the parent of the passed outlines.
            level (int): the level of the passed outlines.
        """
        prev = None
        count = 0
        obj = None
        for outline in outlines:
            count += 1

            obj = self.base.add({
                'Title': outline['text'],
                'Parent': parent.id,
                'Dest': outline['label']
            })

            if prev is not None:
                obj['Prev'] = prev.id
                prev['Next'] = obj.id
            else:
                parent['First'] = obj.id

            prev = obj

            children = outline.get('children', [])
            if len(children) > 0:
                count_ = self._build_outlines_tree(children, obj, level - 1)
                if level > 1:
                    count += count_
                    obj['Count'] = count_
                else:
                    obj['Count'] = -1

        parent['Last'] = obj.id
        return count

    def _build_outlines(self) -> None:
        """Method to create and add the outlines tree to the document.
        """
        if len(self.outlines) == 0:
            return

        obj = self.base.add({
            'Type': b'/Outlines'
        })
        self.root['PageMode'] = b'/UseOutlines'
        self.root['Outlines'] = obj.id
        n = self._build_outlines_tree(self.outlines, obj, self.outlines_level)
        obj['Count'] = n

    def output(self, buffer: Any) -> None:
        """Method to create the PDF file.

        Args:
            buffer (file_like): a file-like object to write the PDF file into.

        Raises:
            Exception: if this document doesn't have any pages.
        """
        if len(self.pages) == 0:
            raise Exception("pdf doesn't have any pages")
        self._build_pages_tree(self.pages)
        self._build_dests()
        self._build_outlines()
        self.base.output(buffer)

from .base import PDFBase
from .content import PDFContent
from .fonts import PDFFonts
from .image import PDFImage
from .page import PDFPage
from .parser import PDFObject
from .table import PDFTable
from .text import PDFText
from .utils import (
    create_graphics, get_page_size, get_paragraph_stream, parse_margin,
    parse_style_str, process_style, to_roman, copy
)
