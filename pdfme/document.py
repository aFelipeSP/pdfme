from collections import defaultdict
from typing import Any, Iterable, Union

from pdfme.utils import parse_range_string

STYLE_PROPS = dict(
    f='font_family', s='font_size', c='font_color', text_align='text_align',
    line_height='line_height', indent='indent'
)

PAGE_PROPS = ('page_size', 'rotate_page', 'margin')
PAGE_NUMBERING = ('page_numbering_offset', 'page_numbering_style')

class PDFDocument:
    """Class that helps to build a PDF document from a dict (``document``
    argument) describing the document contents.

    This class uses an instance of :class:`pdfme.pdf.PDF` internally to build
    the PDF document, but adds some functionalities to allow the user to
    build a PDF document from a JSONish dict, add footnotes and other
    functions explained here.

    A document is made up of sections, that can have their own page layout,
    page numbering, running sections and style.

    ``document`` dict can have the following keys:

    * ``style``: the default style of each section inside the document. A dict
      with all of the keys that a content box can have (see
      :class:`pdfme.content.PDFContent` for more information about content
      box, and for the default values of the attributes of this dict see
      :class:`pdfme.pdf.PDF`). Additional to the keys of content box style, you
      can add the following keys: ``outlines_level``, ``page_size``,
      ``rotate_page``, ``margin``, ``page_numbering_offset`` and
      ``page_numbering_style``. For more information about this page attributes
      and their default values see :class:`pdfme.pdf.PDF` definition.

    * ``formats``: a dict with the global styles of the document that can be
      used anywhere in the document. For more information about this dict
      see :class:`pdfme.pdf.PDF` definition.

    * ``running_sections``: a dict with the running sections that will be used
      by each section in the document. Each section can have, in turn, a
      ``running_section`` list, with the name of the running sections defined in
      this argument that should be included in the section. For information
      about running sections see :class:`pdfme.pdf.PDF`.
      If ``width`` key is equal to ``'left'``, it takes the value of the left
      margin, if equal to ``'right'`` it takes the value of the right margin, if
      equal to ``'full'`` it takes the value of the whole page width, and if it
      is not defined or is None it will take the value of the content width of
      the page.
      If ``height`` key is equal to ``'top'``, it takes the value of the top
      margin, if equal to ``'bottom'`` it takes the value of the bottom margin,
      if equal to ``'full'`` it takes the value of the whole page height, and if
      it is not defined or is None it will take the value the content height of
      the page.
      If ``x`` key is equal to ``'left'``, it takes the value of the left
      margin, if equal to ``'right'`` it takes the value of the whole page width
      minus the right margin, and if it is not defined or is None it will be 0.
      If ``y`` key is equal to ``'top'``, it takes the value of the top
      margin, if equal to ``'bottom'`` it takes the value of the whole page
      height minus the bottom margin, and if it is not defined or is None i
      will be 0.

    * ``per_page``: a list of dicts, each with a mandatory key ``pages``, a
      comma separated string of indexes or ranges (python style), and any of the
      following optional keys:

      * ``style``: a style dict with page related style properties (page_size,
        rotate_page, margin) that will be applied to every page in the ``pages``
        ranges.
      * ``running_sections``: a dict with optional ``exclude`` and ``include``
        lists of running sections names to be included and excluded in every
        page in the ``pages`` ranges.

    * ``sections``: an iterable with the sections of the document.

    Each section in ``sections`` iterable is a dict like the one that can be
    passed to :class:`pdfme.content.PDFContent`, so each section ends up being
    a content box. This class will add as many pages as it is needed to add
    all the contents of every section (content box) to the PDF document.
    
    Additional to the keys from a content box dict, you can
    include a ``running_sections`` list with the name of the
    running sections that you want to be included in all of the pages of the
    section. There is a special key that you can include in a section's
    ``style`` dict called ``page_numbering_reset``, that if True, resets
    the numbering of the pages.

    You can also include footnotes in any paragraph, by adding a dict with the
    key ``footnote`` with the description of the footnote as its value, to the
    list of elements of the dot key (see :class:`pdfme.text.PDFText` for more
    informarion about the structure of a paragraph and the dot key).

    Here is an example of a document dict, and how it can be used to build a
    PDF document using the helper function :func:`pdfme.document.build_pdf`.

    .. code-block:: python

        from pdfme import build_pdf

        document = {
            "style": {
                "page_size": "letter", "margin": [70, 60],
                "s": 10, "c": 0.3, "f": "Times", "text_align": "j",
                "margin_bottom": 10
            },
            "formats": {
                "link": {"c": "blue", "u": True},
                "title": {"s": 12, "b": True}
            },
            "running_sections": {
                "header": {
                    "x": "left", "y": 40, "height": "top",
                    "content": ["Document with header"]
                },
                "footer": {
                    "x": "left", "y": "bottom", "height": "bottom",
                    "style": {"text_align": "c"},
                    "content": [{".": ["Page ", {"var": "$page"}]}]
                }
            },
            "sections": [
                {
                    "running_sections": ["header", "footer"],
                    "style": {"margin": 60},
                    "content": [
                        {".": "This is a title", "style": "title"},
                        {".": [
                            "Here we include a footnote",
                            {"footnote": "Description of a footnote"},
                            ". And here we include a ",
                            {
                                ".": "link", "style": "link",
                                "uri": "https://some.url.com"
                            }
                        ]}
                    ]
                },
                {
                    "running_sections": ["footer"],
                    "style": {"rotate_page": True},
                    "content": [
                        "This is a rotated page"
                    ]
                }
            ]
        }

        with open('document.pdf', 'wb') as f:
            build_pdf(document, f)

    Args:
        document (dict): a dict like the one just described.
        context (dict, optional): a dict containing the context of the inner
            :class:`pdfme.pdf.PDF` instance.
    """
    def __init__(self, document: dict, context: dict=None) -> None:
        context = {} if context is None else context
        style = copy(document.get('style', {}))
        style_args = {
            v: style[k] for k, v in STYLE_PROPS.items() if k in style
        }

        page_args = {
            k: style[k] for k in PAGE_PROPS + PAGE_NUMBERING if k in style
        }

        self.pdf = PDF(
            outlines_level=style.get('outlines_level', 1),
            **page_args, **style_args
        )

        self.style = style

        self.pdf.context.update(context)

        self.pdf.formats = {}
        self.pdf.formats['$footnote'] = {'r': 0.5, 's': 6}
        self.pdf.formats['$footnotes'] = {'s': 10, 'c': 0}
        self.pdf.formats.update(document.get('formats', {}))

        self.running_sections = document.get('running_sections', {})

        self.per_page = []
        for range_dict in document.get('per_page', []):
            new_range_dict = copy(range_dict)
            new_range_dict['pages'] = parse_range_string(range_dict['pages'])
            self.per_page.append(new_range_dict)

        self.sections = document.get('sections', [])

        self.x = self.y = self.width = self.height = 0

        self.footnotes = []
        self._traverse_document_footnotes(self.sections)

        self.footnotes_margin = 10

    def _traverse_document_footnotes(
        self, element: Union[list, tuple, dict]
    ) -> None:
        """Method to traverse the document sections, trying to find footnotes
        dicts, to prepare them for being processed by the inner PDF instance.

        Args:
            element (list, tuple, dict): the element to be tarversed.

        Raises:
            TypeError:
        """
        if isinstance(element, (list, tuple)):
            for child in element:
                self._traverse_document_footnotes(child)
        elif isinstance(element, dict):
            if 'footnote' in element:
                element.setdefault('ids', [])
                name = '$footnote:' + str(len(self.footnotes))
                element['ids'].append(name)
                element['style'] = '$footnote'
                element['var'] = name
                self.pdf.context[name] = '0'

                footnote = element['footnote']

                if not isinstance(footnote, (dict, str, list, tuple)):
                    footnote = str(footnote)
                if isinstance(footnote, (str, list, tuple)):
                    footnote = {'.': footnote}

                if not isinstance(footnote, dict):
                    raise TypeError(
                        'footnotes must be of type dict, str, list or tuple:{}'
                        .format(footnote)
                    )

                self.footnotes.append(footnote)
            else:
                for value in element.values():
                    if isinstance(value, (list, tuple, dict)):
                        self._traverse_document_footnotes(value)

    def _set_running_sections(
        self, running_sections: Iterable, page_width: 'Number',
        page_height: 'Number', margin: dict
    ):
        """Method to set the running sections for every section in the document.

        Args:
            running_sections (list, tuple): the list of the running sections
                of the current section being added.
        """
        self.pdf.running_sections = []
        for name in running_sections:
            section = copy(self.running_sections[name])

            if section.get('width') in ['left', 'right']:
                section['width'] = margin[section.get('width')]
            if section.get('width') == 'full':
                section['width'] = page_width
            if section.get('height') in ['top', 'bottom']:
                section['height'] = margin[section.get('height')]
            if section.get('height') == 'full':
                section['height'] = page_height
            if section.get('x') == 'left':
                section['x'] = margin['left']
            if section.get('x') == 'right':
                section['x'] = page_width - margin['right']
            if section.get('y') == 'top':
                section['y'] = margin['top']
            if section.get('y') == 'bottom':
                section['y'] = page_height - margin['bottom']

            width = section.get('width', (
                page_width - margin['right'] - margin['left']
            ))
            height = section.get('height', (
                page_height - margin['top'] - margin['bottom']
            ))
            x = section.get('x', 0)
            y = section.get('y', 0)
            self.pdf.add_running_section(section, width, height, x, y)

    def run(self) -> None:
        """Method to process this document sections.
        """
        for section in self.sections:
            self._process_section(section)

    def _process_section(self, section: dict) -> None:
        """Method to process a section from this document.

        Args:
            section (dict): a dict representing the section to be processed.
        """
        section_style = copy(self.style)
        section_style.update(process_style(section.get('style', {}), self.pdf))
        
        if 'page_numbering_offset' in section_style:
            self.pdf.page_numbering_offset = section_style['page_numbering_offset']
        if 'page_numbering_style' in section_style:
            self.pdf.page_numbering_style = section_style['page_numbering_style']
        if section_style.get('page_numbering_reset', False):
            self.pdf.page_numbering_offset = -len(self.pdf.pages)

        section['style'] = section_style

        self.section = self.pdf._create_content(
            section, self.width, self.height, self.x, self.y
        )

        section_page_args = {
            k: section_style[k] for k in PAGE_PROPS if k in section_style
        }

        while True:
            page_n = len(self.pdf.pages)

            page_args = section_page_args.copy()

            running_sections = set(section.get('running_sections', []))

            for range_dict in self.per_page:
                if page_n in range_dict['pages']:
                    if 'style' in range_dict:
                        page_style = range_dict['style']
                        page_args.update({
                            k: page_style[k] for k in PAGE_PROPS
                            if k in page_style
                        })
                    if 'running_sections' in range_dict:
                        per_page_rs = range_dict['running_sections']
                        running_sections -= set(per_page_rs.get('exclude', []))
                        running_sections.update(
                            set(per_page_rs.get('include', []))
                        )

            self.pdf.setup_page(**page_args)

            page_width, page_height = self.pdf.page_width, self.pdf.page_height
            if self.pdf.rotate_page:
                page_width, page_height = page_height, page_width

            self.x = self.pdf.margin['left']
            self.width = page_width - self.pdf.margin['right'] - self.x
            self.y = page_height - self.pdf.margin['top']
            self.height = self.y - self.pdf.margin['bottom']

            self.section.setup(self.x, self.y, self.width, self.height)

            self._set_running_sections(
                running_sections, page_width, page_height, self.pdf.margin
            )

            self.pdf.add_page()

            self._add_content()

            if self.section.finished:
                break

    def _add_content(self) -> None:
        """Method to add the section contents to the current page.

        Raises:
            Exception: if the footnotes added to the page are very large.
        """

        section_state = self.section.get_state() \
            if self.section.pdf_content_part is not None else {
                'section_element_index': 0,
                'section_delayed': [],
                'children_memory': []
            }

        self.section.run(height=self.height)
        footnotes_obj = self._process_footnotes()

        if footnotes_obj is None:
            self.pdf._add_graphics([*self.section.fills,*self.section.lines])
            self.pdf._add_parts(self.section.parts)
            self.pdf.page._y -= self.section.current_height
        else:
            footnotes_height = footnotes_obj.current_height
            if footnotes_height >= self.height - self.footnotes_margin - 20:
                raise Exception(
                    "footnotes are very large and don't fit in one page"
                )
            new_height = self.height - footnotes_obj.current_height \
                - self.footnotes_margin

            if section_state is not None:
                self.section.set_state(**section_state)
                self.section.finished = False
            self.pdf._content(self.section, height=new_height)

            footnotes_obj = self._process_footnotes()

            if footnotes_obj is not None:
                self.pdf.page._y = self.pdf.margin['bottom'] + footnotes_height
                self.pdf.page.x = self.x

                x_line = round(self.pdf.page.x, 3)
                y_line = round(self.pdf.page._y + self.footnotes_margin/2, 3)
                self.pdf.page.add(' q 0 G 0.5 w {} {} m {} {} l S Q'.format(
                    x_line, y_line, x_line + 150, y_line
                ))
                self.pdf._content(footnotes_obj, height=self.height)

    def _check_footnote(self, ids: dict, page_footnotes: list) -> None:
        """Method that extract the footnotes from the ids passed as argument,
        and adds them to the ``page_footnotes`` list argument.

        Args:
            ids (dict): the ids list.
            page_footnotes (list): the list of the page footnotes to save the
                footnotes found in the ids.
        """
        for id_, rects in ids.items():
            if len(rects) == 0:
                continue
            if id_.startswith('$footnote:'):
                index = int(id_[10:])
                page_footnotes.append(self.footnotes[index])
                self.pdf.context[id_] = len(page_footnotes)

    def _check_footnotes(self, page_footnotes: list) -> None:
        """Method that loops through the current section parts, extracting the
        footnotes from each part's ids.

        Args:
            page_footnotes (list): the list of the page footnotes to save the
                footnotes found in the ids.
        """
        for part in self.section.parts:
            if part['type'] == 'paragraph':
                self._check_footnote(part['ids'], page_footnotes)

    def _get_footnotes_obj(self, page_footnotes: list) -> 'PDFContent':
        """Method to create the PDFContent object containing the footnotes of
        the current page.

        Args:
            page_footnotes (list): the list of the page footnotes

        Returns:
            PDFContent: object containing the footnotes.
        """
        content = {'style': '$footnotes', 'content': []}
        for index, footnote in enumerate(page_footnotes):
            footnote = copy(footnote)
            style = footnote.setdefault('style', {})
            style.update(dict(
                list_text=str(index + 1) + ' ', list_style='$footnote'
            ))
            content['content'].append(footnote)

        footnote_obj = self.pdf._create_content(
            content, self.width, self.height, self.x, self.y
        )
        footnote_obj.run()
        return footnote_obj

    def _process_footnotes(self) -> 'PDFContent':
        """Method to extract the footnotes from the current section parts, and
        create the PDFContent object containing the footnotes of
        the current page.

        Returns:
            PDFContent: object containing the footnotes.
        """
        page_footnotes = []
        self._check_footnotes(page_footnotes)
        if len(page_footnotes) == 0:
            return None
        return self._get_footnotes_obj(page_footnotes)

    def output(self, buffer: Any) -> None:
        """Method to create the PDF file.

        Args:
            buffer (file_like): a file-like object to write the PDF file into.
        """
        self.pdf.output(buffer)

def build_pdf(document: dict, buffer: Any, context: dict=None) -> None:
    """Function to build a PDF document using a PDFDocument instance. This is
    the easiest way to build a PDF document file in this library. For more
    information about arguments ``document``, and ``context`` see
    :class:`pdfme.document.PDFDocument`.

    Args:
        buffer (file_like): a file-like object to write the PDF file into.
    """
    doc = PDFDocument(document, context)
    doc.run()
    doc.output(buffer)

from .content import Number, PDFContent
from .pdf import PDF
from .utils import process_style, copy