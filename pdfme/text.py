import json
import re
from typing import Optional, Union
from uuid import uuid4

PARAGRAPH_DEFAULTS = {'text_align': 'l', 'line_height': 1.1, 'indent': 0}
TEXT_DEFAULTS = {'f': 'Helvetica', 'c': 0.1, 's': 11, 'r': 0, 'bg': None}

ContentType = Union[str, list, tuple, dict]
Number = Union[int, float]
class PDFState:
    """Class that represents the state of a paragraph line part.

    The state is a lower level version of the style, and is used by the other
    paragraph classes to make calculations and yield the paragraph PDF stream.

    Args:
        style (dict): the paragraph line part style.
        fonts (PDFFonts): the fonts instance with the information about
            the fonts already added to the PDF document.
    """
    def __init__(self, style: dict, fonts: 'PDFFonts') -> None:
        self.font_family = style['f']

        f_mode = ''
        if style.get('b', False):
            f_mode += 'b'
        if style.get('i', False):
            f_mode += 'i'
        if f_mode == '':
            f_mode = 'n'
        self.font_mode = 'n' if not f_mode in fonts.fonts[style['f']] else f_mode

        self.font = fonts.get_font(self.font_family, self.font_mode)

        self.size = style['s']
        self.color = PDFColor(style['c'])
        self.rise = style.get('r', 0) * self.size

    def compare(self, other: Optional['PDFState']) -> str:
        """Compares this state, with state ``other`` and returns a PDF stream
        with the differences between both states.

        Args:
            other (PDFState): the state to compare.

        Returns:
            str: a PDF stream with the differences between both states.
        """
        ret_value = ''
        if (
            other is None or self.font_family != other.font_family or
            self.font_mode != other.font_mode or self.size != other.size
        ):
            ret_value += ' /{} {} Tf'.format(self.font.ref, round(self.size, 3))
        if other is None or self.color != other.color:
            ret_value += ' ' + str(self.color)
        if other is None or self.rise != other.rise:
            ret_value += ' {} Ts'.format(round(self.rise, 3))

        return ret_value

class PDFTextLinePart:
    """This class represents a part of a paragraph line, with its own style.

    Args:
        style (dict): the style of this line part.
        fonts (PDFFonts): the fonts instance with the information about
            the fonts already added to the PDF document.
        ids (list, optional): the ids of this part.
    """
    def __init__(self, style: dict, fonts: 'PDFFonts', ids: list=None) -> None:
        self.fonts = fonts

        self.style = style
        self.state = PDFState(style, fonts)
        self.underline = style.get('u', False)
        self.background = PDFColor(style.get('bg'))
        self.ids = [] if id is None else ids
        self.width = 0
        self.words = []

        self.space_width = self.get_char_width(' ')
        self.spaces_width = 0

    def pop_word(self, index: int=None) -> Optional[str]:
        """Function to delete the last word of this part if ``index`` is None,
        and the word in the position ``index`` if it's not None.

        Args:
            index (int, optional): word index.

        Returns:
            str: if word in ``index`` could be deleted, the deleted word is
                returned, if not None is returned.
        """
        if len(self.words) > 0:
            word = self.words.pop() if index is None else self.words.pop(index)
            if word == ' ':
                self.spaces_width -= self.space_width
            else:
                self.width -= self.get_word_width(word)
            return word

    def add_word(self, word: str) -> None:
        """Function to add a word to this part.

        Args:
            word (str): the word.
        """
        self.words.append(word)
        if word == ' ':
            self.spaces_width += self.space_width
        else:
            self.width += self.get_word_width(word)

    def current_width(self, factor: Number=1) -> float:
        """Return the width of this part, according to the words added to this
        part, using ``factor`` to calculate this width of the spaces in this
        part.

        Args:
            factor (int, float, optional): to calculate this width of the spaces
                in this part.

        Returns:
            float: width of this part.
        """
        return self.width + self.spaces_width*factor

    def tentative_width(self, word: str, factor: Number=1) -> float:
        """The same as method ``current_width``, but adding the width of
        ``word``.

        Args:
            word (str): the word that could be added to this part.
            factor (int, float, optional): to calculate this width of the spaces
                in this part.

        Returns:
            float: the width of this part + the width of the word passed.
        """
        word_width = self.space_width * factor if word == ' ' else \
            self.get_word_width(word)
        return self.current_width(factor) + word_width

    def get_char_width(self, char: str) -> float:
        """The width of the character passed.

        Args:
            char (str): the character string.

        Returns:
            float: the width of the character passed.
        """
        return self.state.size * self.state.font.get_char_width(char)

    def get_word_width(self, word: str) -> float:
        """The width of the word passed.

        Args:
            char (str): the word string.

        Returns:
            float: the width of the word passed.
        """
        return self.state.size * self.state.font.get_text_width(word)

class PDFTextLine:
    """Class that represents a line of a paragraph.

    This class has the logic to add paragraph parts, and inside them add their
    words one by one, until all of the horizontal space of the paragraph has
    been used. For more information about this mechanism check the method
    :meth:`pdfme.text.PDFTextLine.add_word`.

    Args:
        fonts (PDFFonts):  to extract information about the fonts
            being used in the paragraph.
        max_width (int, float, optional): the maximum horizontal space that this
            line can use.
        text_align (str, optional): ``'l'`` for left (default), ``'c'`` for
            center, ``'r'`` for right and ``'j'`` for justified text.
        top_margin (Number, optional): if not None, this is the top margin of
            the line, added to the actual line height.
    """
    def __init__(
        self, fonts: 'PDFFonts', max_width: Number=0, text_align: str=None,
        top_margin: Number=0
    ) -> None:
        self.fonts = fonts
        self.max_width = max_width
        self.line_parts = []

        self.justify_min_factor = 0.7
        self.text_align = PARAGRAPH_DEFAULTS['text_align'] \
            if text_align is None else text_align

        self.factor = 1 if self.text_align != 'j' else self.justify_min_factor

        self.top_margin = top_margin
        self.next_line = None
        self.is_last_word_space = True
        self.firstWordAdded = False
        self.started = False

    @property
    def height(self) -> float:
        """Property that returns the line height, calculated from the vertical
        space of each part of the line.

        Returns:
            float: the line height.
        """
        top = 0
        height_ = 0
        for part in self.line_parts:
            if part.state.rise > 0 and part.state.rise > top:
                top = part.state.rise
            if part.state.size > height_:
                height_ = part.state.size

        return height_ + self.top_margin + top

    @property
    def min_width(self) -> float:
        """Property that returns the width of the line, calculated using the
        minimum value for attribute ``factor``. This attribute is used to
        increase or decrease the space character width inside a line to

        Returns:
            float: the line width.
        """
        ws = self.get_widths()
        return ws[0] + ws[1] * self.factor

    @property
    def bottom(self) -> float:
        """Property that returns the line bottom, calculated from the vertical
        space of each part of the line.

        Returns:
            float: the line bottom.
        """
        bottom = 0
        for part in self.line_parts:
            if part.state.rise < 0 and -part.state.rise > bottom:
                bottom = -part.state.rise
        return bottom

    def get_widths(self) -> tuple:
        """This function returns the widths of the line.

        Returns:
            tuple: of 2 elements, the width on the words as the first, and the
                width of the spaces as the second.
        """
        words_width = 0
        spaces_width = 0
        for part in self.line_parts:
            words_width += part.width
            spaces_width += part.spaces_width
        return words_width, spaces_width

    def add_line_part(self, style:dict=None, ids:list=None) -> PDFTextLinePart:
        """Add a new line part to this line.

        Args:
            style (dict, optional): the style of the new part.
            ids (list, optional): the ids of the new part.

        Returns:
            PDFTextLinePart: The new line part that was added.
        """
        if self.next_line is None:
            self.next_line = PDFTextLine(
                self.fonts, self.max_width, self.text_align
            )

        line_part = PDFTextLinePart(style, self.fonts, ids)
        self.next_line.line_parts.append(line_part)
        return line_part

    def add_accumulated(self) -> None:
        """Function to add the parts accumulated in the auxiliar line (
        ``next_line`` attribute) to this line.
        """
        if len(self.line_parts):
            for word in self.next_line.line_parts[0].words:
                self.line_parts[-1].add_word(word)
            self.next_line.line_parts = self.next_line.line_parts[1:]

        self.line_parts.extend(self.next_line.line_parts)
        last_part = self.line_parts[-1]
        last_part.add_word(' ')
        self.next_line.line_parts = [
            PDFTextLinePart(last_part.style, self.fonts, last_part.ids)
        ]

    def add_word(self, word:str) -> dict:
        """Function to add a word to this line.

        Args:
            word (str): The word to be added.

        Returns:
            dict: containing a ``status`` key, with one of the following values:

            * ``'added'``: The word passed was added to the auxiliar line, or
              if the word is a space the accumulated words in the auxiliar line,
              to the current line.

            * ``'ignored'``: The word passed (a space) was ignored.

            * ``'preadded'``: The word passed was added to the auxiliar line.

            * ``'finished'``: The word didn't fit in the current line, and this
              means this line is full. Because of this, a new line is created
              to put this word, and this new line is returned in the key
              ``'new_line'``.

        """
        if not self.started:
            if word.isspace():
                if self.firstWordAdded:
                    self.started = True
                    self.add_accumulated()
                    return {'status': 'added'}
                else:
                    return {'status': 'ignored'}
            else:
                self.firstWordAdded = True
                self.next_line.line_parts[-1].add_word(word)
                return {'status': 'added'}
        else:
            if word.isspace():
                if self.is_last_word_space:
                    return {'status': 'ignored'}
                else:
                    self.add_accumulated()
                    return {'status': 'added'}
            else:
                self.is_last_word_space = False
                self.next_line.line_parts[-1].add_word(word)
                if (self.min_width + self.next_line.min_width < self.max_width):
                    return {'status': 'preadded'}
                else:
                    if (
                        len(self.line_parts[-1].words) and
                        self.line_parts[-1].words[-1] == ' '
                    ):
                        self.line_parts[-1].pop_word(-1)
                    self.next_line.firstWordAdded = True
                    self.next_line.top_margin = self.bottom
                    self.next_line.next_line = PDFTextLine(
                        self.fonts, self.max_width, self.text_align
                    )
                    line_parts = self.next_line.line_parts
                    self.next_line.next_line.line_parts = line_parts
                    self.next_line.line_parts = []
                    return {
                        'status': 'finished', 'new_line': self.next_line
                    }

class PDFTextBase:
    """Class that represents a rich text paragraph to be added to a
    :class:`pdfme.pdf.PDF` instance.

    You should use :class:`pdfme.text.PDFText` instead of this class, because
    it has more functionalities.

    To create the data needed to add this paragraph to the PDF document,
    you have to call the method :meth:`pdfme.text.PDFTextBase.run`, which
    will try to add all of the dict parts in ``content`` argument list (or
    tuple) to the rectangle defined by args ``x``, ``y``, ``width`` and
    ``height``.

    Each part represents a part of the paragraph with a different style or with
    a ``var`` or a specific ``id``.

    The parts are added to this rectangle, until they are all
    inside of it, or until all of the vertical space is used and the rest of
    the parts can not be added. In these two cases method ``run``
    finishes, and the property ``finished`` will be True if all the parts
    were added, and False if the vertical space ran out.
    If ``finished`` is False, you can set a new rectangle (on a new page for
    example) and use method ``run`` again (passing the parameters of the new
    rectangle) to add the remaining parts that couldn't be added in the
    last rectangle. You can keep doing this until all of the parts are
    added and therefore property ``finished`` is True.

    By using method ``run`` the paragraph is not really added to the PDF
    object. After calling ``run``, the property ``result`` will be
    available with the information needed to be added to the PDF, at least
    the parts that fitted inside the rectangle. You have to use the
    property ``result`` to add the paragraph to the PDF object before
    using method ``run`` again (in case ``finished`` is False), because
    it will be redefined for the next rectangle after calling ``run`` again.
    You can check the ``text`` method in `PDF`_ module to see how this
    process is done.

    The other args not defined here, are explained in
    :class:`pdfme.text.PDFText`.

    Args:
        content (str, list, tuple): If this is a string, it will
            become the following:

            .. code-block:: python

                [{'style': <DEFAULT_STYLE>, 'text': <STRING>}]

            If this is a list or a tuple, its elements should be dicts with the
            following keys:

            * ``'text'``: this is the text that will be displayed with the style
              defined in ``style`` key.

            * ``'style'``: this is a style dict like the one described in
              :class:`pdfme.text.PDFText`.

            * ``'ids'``: see :class:`pdfme.text.PDFText` definition.

            * ``'var'``: see :class:`pdfme.text.PDFText` definition.

    Raises:
        TypeError: if ``content`` is not a str, list or tuple.

    .. _PDF: https://github.com/aFelipeSP/pdfme/blob/main/pdfme/pdf.py
    """
    def __init__(
        self, content: Union[str, list, tuple], width: Number, height: Number,
        x: Number=0, y: Number=0, fonts: 'PDFFonts'=None, text_align: str=None,
        line_height: Number=None, indent: Number=0, list_text: str=None,
        list_indent: Number=None, list_style: dict=None, pdf: 'PDF'=None
    ) -> None:
        self.fonts = fonts
        self.setup(x, y, width, height)
        self.indent = indent
        self.text_align = PARAGRAPH_DEFAULTS['text_align'] \
            if text_align is None else text_align
        self.line_height = PARAGRAPH_DEFAULTS['line_height'] \
            if line_height is None else line_height

        self.list_text = list_text
        self.list_indent = list_indent
        self.list_style = list_style
        self.pdf = pdf

        if isinstance(content, str):
            content = [{'style': TEXT_DEFAULTS.copy(), 'text': content}]
        if not isinstance(content, (list, tuple)):
            raise TypeError(
                'content must be of type str, list or tuple: {}'.format(content)
            )

        self.last_part_added = 0
        self.last_part_line = 0
        self.last_part = 0

        self.last_word_added = 0
        self.last_word_line = 0
        self.last_word = 0

        self.content = content
        self.finished = False
        self.is_first_line = True
        self.correct_indent = True
        self.list_setup_done = False

    @property
    def stream(self) -> str:
        """Property that returns the PDF stream generated by the method ``run``,
        with all of the graphics and the text, ready to be added to a PDF page
        stream.

        Returns:
            str: the stream.
        """
        return get_paragraph_stream(self.x, self.y, self.text, self.graphics)

    @property
    def result(self) -> dict:
        """Property that returns a dict with the result of calling method
        ``run``, and can be passed to method
        :meth:`pdfme.pdf.PDF._add_text`, to add this paragraph to that
        PDF document's page. Check method ``_add_parts`` from
        :class:`pdfme.pdf.PDF` to see how a dict like the one returned by
        this method (a paragraph part) is added to a PDF instance.

        The dict returned will have the following keys:

        * ``x`` the x coordinate.

        * ``y`` the y coordinate.

        * ``width`` of the paragraph.

        * ``height`` of the paragraph.

        * ``text_stream`` a string with the paragraphs PDF text stream.

        * ``graphics_stream`` a string with the paragraphs PDF graphics stream.

        * ``used_fonts`` a set with tuples of 2 elements, first element the
          font family, and second element the font mode.

        * ``ids`` a dict with every id extracted from the paragraph.

        Returns:
            dict: like the one described.

        .. _PDF: https://github.com/aFelipeSP/pdfme/blob/main/pdfme/pdf.py
        """

        return dict(
            x=self.x, y=self.y, width=self.width, height=self.current_height,
            text_stream=self.text, graphics_stream=self.graphics,
            used_fonts=self.used_fonts, ids=self.ids,
        )

    def get_state(self) -> dict:
        """Method to get the current state of this paragraph. This can be used
        later in method :meth:`pdfme.text.PDFText.set_state` to
        restore this state in this paragraph (like a checkpoint in a
        videogame).

        Returns:
            dict: a dict with the state of this paragraph.
        """
        return {
            'last_part': self.last_part,
            'last_word': self.last_word
        }

    def set_state(self, last_part: int=None, last_word: int=None) -> None:
        """Function to update the state of the paragraph

        The arguments of this method define the current state of this paragraph,
        and with this method you can change that state.

        Args:
            last_part (int): this is the index of the part that was being
                processed the last time method ``run`` was called.
            last_word (int): this is the index of the
                word of the last part that was added the last time method
                ``run`` was called.
        """
        self.last_part = last_part
        self.last_word = last_word

    def setup(
        self, x: Number=None, y:Number=None, width: Number=None,
        height: Number=None
    ):
        """Function to change any or all of the parameters of the rectangle of
        the content.

        Args:
            x (int, float, optional): The x coordinate of the left of the
                rectangle.
            y (int, float, optional): The y coordinate of the top of the
                rectangle.
            width (int, float, optional): The width of the rectangle where the
                contents will be arranged.
            height (int, float, optional): The height of the rectangle where the
                contents will be arranged.
            last_part (int, optional): If not None, this is the index of the
                part that was being processed the last time method ``run`` was
                called.
            last_word (int, optional): If not None, this is the index of the
                word of the last part that was added the last time method
                ``run`` was called.
        """
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

    def init(self) -> None:
        """Function to reset all of the instance properties that have to be
        resetted before running the arranging process in a new rectangle.

        This function is called by method ``run``.
        """
        self.started = False
        self.lines = []
        self.text = ''
        self.graphics = ''
        self.ids = {}
        self.first_line_added = False

        self.used_fonts = set()
        self.current_line_used_fonts = set()
        self.current_height = 0
        self.lines = []

        line_width = self.width - (self.indent if self.is_first_line else 0)
        self.current_line = PDFTextLine(
            self.fonts, line_width, self.text_align, self.line_height
        )

        self.last_indent = 0
        self.last_state = self.last_factor = self.last_fill = None
        self.last_color = self.last_stroke_width = None

        self.y_ = 0

    def run(
        self, x: Number=None, y: Number=None, width: Number=None,
        height: Number=None
    ) -> dict:
        """Function to create the data needed to add this paragraph to the PDF
        document.

        This function will try to add all of the dict parts in ``content``
        argument list (or tuple) to this paragraph rectangle. Check this class
        documentation for more information about this method.

        This function args are the same as
        :meth:`pdfme.text.PDFTextBase.setup`.

        Returns:
            dict: The dict from the property ``result``.
        """
        self.setup(x, y, width, height)
        self.init()
        for part_index in range(self.last_part, len(self.content)):
            part = self.content[part_index]
            if not isinstance(part, dict):
                raise TypeError(
                    'elements in content must be of type dict: {}'
                    .format(part)
                )
            if 'type' in part:
                if part['type'] == 'br':
                    self.last_part_added = part_index + 1
                    self.last_word_added = 0
                    continue_ = self.add_current_line(True)
                    self.current_line = PDFTextLine(
                        self.fonts, self.width, self.text_align,
                        self.line_height
                    )
                    if not continue_:
                        return self.result
            else:
                continue_ = self.add_part(part, part_index)
                if not continue_:
                    return self.result

        continue_ = self.add_current_line(True)
        if continue_:
            self.finished = True
        return self.result

    def add_part(self, part: dict, part_index: int) -> bool:
        """Function used by methodm ``run`` to add one paragraph part at a time.

        Args:
            part (dict): part to be added.
            part_index (int): index of the part to be added.

        Returns:
            bool: whether it was able to add all of the parts (True) or the
                vertical space ran out.
        """

        if 'var' in part and self.pdf:
            part['text'] = str(self.pdf.context.get(part['var'], ''))

        words = part.get('text')
        if not isinstance(words, (str, list, tuple)):
            return 'continue'

        style = TEXT_DEFAULTS.copy()
        style.update(part.get('style', {}))
        new_line_part = self.current_line.add_line_part(
            style=style, ids=part.get('ids')
        )

        if not self.list_setup_done and self.list_text:
            self.list_setup_done = True
            self.setup_list()

        self.current_line_used_fonts.add((
            new_line_part.state.font_family,
            new_line_part.state.font_mode
        ))

        if isinstance(words, str):
            part['text'] = words = [
                ' ' if w.isspace() else w
                for w in re.split('( +)', words)
                if w != ''
            ]
        is_last_part = part_index == len(self.content) - 1

        for word_index in range(self.last_word, len(words)):
            word = words[word_index]
            ans = self.current_line.add_word(word)
            if ans['status'] == 'added':
                self.last_part_added = part_index
                self.last_word_added = word_index + 1
            elif ans['status'] == 'finished':
                continue_ = self.add_current_line(
                    is_last_part and word_index == len(words) - 1
                )
                ans['new_line'].max_width = self.width - (
                    self.list_indent if self.list_text else 0
                )
                ans['new_line'].next_line.max_width = ans['new_line'].max_width
                self.current_line = ans['new_line']
                if not continue_:
                    return False

        self.last_word = 0
        return True

    def add_current_line(self, is_last: bool=False) -> bool:
        """Function to add the current line to the list of already added lines.

        Args:
            is_last (bool, optional): whether this is the last line of this
                paragraph (True) or not (False).

        Returns:
            bool: whether this line was successfully added (True) or not (False)
        """
        if is_last and self.current_line.next_line is not None:
            self.current_line.line_parts.extend(
                self.current_line.next_line.line_parts
            )

        line_height = self.current_line.height
        if self.first_line_added:
            line_height *= self.line_height
        else:
            self.first_line_added = True

        if line_height + self.current_height > self.height:
            self.last_part = self.last_part_line
            self.last_word = self.last_word_line
            return False
        else:
            self.last_part_line = self.last_part_added
            self.last_word_line = self.last_word_added
            self.current_height += line_height
            self.lines.append(self.current_line)
            self.used_fonts.update(self.current_line_used_fonts)
            self.current_line_used_fonts = set()

            self.add_line_to_stream(self.current_line, is_last)
            self.current_line = None

            return True

    def setup_list(self) -> None:
        """This function is called when the first part of the paragraph is going
        to be added, and if this is a list paragraph, i.e. a paragraph with a
        something on its left (a bullet, a number, etc), this function will
        setup everything needed to display the text of the list paragraph, and
        will adjust its width to make space for the list text.

        Raises:
            TypeError: if list_style or list_indent passed to this instance
                are not a dict and an number respectively.
        """
        style = self.current_line.next_line.line_parts[0].style.copy()

        if self.list_style is None:
            self.list_style = {}
        elif isinstance(self.list_style, str):
            self.list_style = process_style(self.list_style, self.pdf)

        if not isinstance(self.list_style, dict):
            raise TypeError(
                'list_style must be a str or a dict. Value: {}'
                .format(self.list_style)
            )

        style.update(self.list_style)
        line_part = PDFTextLinePart(style, self.fonts)

        self.current_line_used_fonts.add(
            (line_part.state.font_family, line_part.state.font_mode)
        )

        if self.list_indent is None:
            self.list_indent = line_part.get_word_width(str(self.list_text))
        elif not isinstance(self.list_indent, (float, int)):
            raise TypeError(
                'list_indent must be int or float. Value: {}'
                .format(self.list_indent)
            )

        self.list_state = line_part.state
        self.current_line.max_width -= self.list_indent

    def add_line_to_stream(self, line: PDFTextLine, is_last:bool=False) -> None:
        """Function to add a PDFTextLine representing a paragraph line to the
        already added lines stream.

        Args:
            line (PDFTextLine): The line to be added to the stream.
            is_last (bool, optional): whether this is the last line of this
                paragraph (True) or not (False).
        """
        words_width, spaces_width = line.get_widths()
        x = self.list_indent if self.list_text else 0
        line_height = line.height
        full_line_height = line_height
        ignore_factor = self.text_align != 'j' or is_last or spaces_width == 0
        factor_width = self.width - words_width - x
        adjusted_indent = 0
        if self.text_align in ['r', 'c']:
            indent = self.width - words_width - spaces_width
            if self.text_align == 'c':
                indent /= 2
            x += indent
            adjusted_indent = indent - self.last_indent
            self.last_indent = indent

        if not self.started:
            self.started = True
            if self.is_first_line:
                factor_width -= self.indent
                x += self.indent
                self.is_first_line = False

                first_indent = (
                    adjusted_indent if self.text_align in ['r', 'c']
                    else self.indent
                )

                if self.list_text:
                    first_indent += self.list_indent
                    if self.list_state.size > full_line_height:
                        full_line_height = self.list_state.size
                    self.text += ' 0 -{} Td{} ({})Tj {} 0 Td'.format(
                        round(full_line_height, 3),
                        self.list_state.compare(self.last_state),
                        self.list_text, first_indent
                    )
                else:
                    self.text += ' {} -{} Td'.format(
                        round(first_indent, 3), round(full_line_height, 3)
                    )
            else:
                first_indent = adjusted_indent
                if self.list_text:
                    first_indent += self.list_indent
                self.text += ' {} -{} Td'.format(
                    round(first_indent, 3), round(full_line_height, 3)
                )
        else:
            if self.correct_indent:
                self.correct_indent = False
                adjusted_indent -= self.indent

            full_line_height *= self.line_height

            self.text += ' {} -{} Td'.format(round(adjusted_indent, 3),
                                        round(full_line_height, 3))

        self.y_ -= full_line_height

        factor = 1 if ignore_factor else factor_width / spaces_width

        for part in line.line_parts:
            text = self.clean_words(part.words)
            self.text += self.output_text(part, text, factor)
            part_width = part.current_width(factor)
            part_size = round(part.state.size, 3)

            if text != '' and not text.isspace():
                if part.ids is not None:
                    for id_ in part.ids:
                        id_y = self.y_ + part.state.rise - part_size*0.25
                        self.ids.setdefault(id_, []).append([
                            round(x, 3), round(id_y, 3),
                            round(x + part_width, 3), round(id_y + part_size, 3)
                        ])

                part_graphics = self.output_graphics(
                    part, x, self.y_, part_width
                )
                self.graphics += part_graphics
            x += part_width

    def clean_words(self, words: list) -> str:
        """This function joins a list of words (spaces included) and makes the
        resulting string compatible with a PDF string.

        Args:
            words (list): a list of strings, where each string is a word.

        Returns:
            str: A string with all of the words passed.
        """

        text = ''.join(word for word in words)
        if text != '':
            text = text.replace('\\',r'\\').replace('(','\(').replace(')','\)')
        return text

    def output_text(self, part: PDFTextLinePart, text, factor: Number=1) -> str:
        """Function that creates a piece of PDF stream (only the text), from
        the PDFTextLinePart and the ``text`` arguments.

        Args:
            part (PDFTextLinePart): the part to be transformed into a string
                representing a PDF stream piece.
            text ([type]): the text to be transformed into a string
                representing a PDF stream piece.
            factor (Number, optional): factor of the line needed to create
                center, right and justified aligned paragraphs.

        Returns:
            str: representing the PDF stream
        """
        stream = part.state.compare(self.last_state)
        self.last_state = part.state

        tw = round(part.space_width * (factor - 1), 3)
        if self.last_factor != tw:
            if tw == 0:
                tw = 0
            stream += ' {} Tw'.format(tw)
            self.last_factor = tw

        if text != '':
            # TODO: How can we add unicode to PDF string
            stream += ' ({})Tj'.format(text)
        return stream

    def output_graphics(
        self, part: PDFTextLinePart, x: Number, y: Number, part_width: Number
    ) -> str:
        """Function that creates a piece of PDF stream (only the graphics),
        from the PDFTextLinePart argument.

        Args:
            part (PDFTextLinePart): the part to be transformed into a string
                representing a PDF stream piece.
            x (int, float): the x origin coordinate of the graphics being added.
            y (int, float): the y origin coordinate of the graphics being added.
            width (int, float): the width of the part being added

        Returns:
            str: representing the PDF stream
        """
        graphics = ''
        if part.background is not None and not part.background.color is None:
            if part.background != self.last_fill:
                self.last_fill = part.background
                graphics += ' ' + str(self.last_fill)

            graphics += ' {} {} {} {} re F'.format(
                round(x, 3),
                round(y + part.state.rise - part.state.size*0.25, 3),
                round(part_width, 3), round(part.state.size*1.2, 3)
            )

        if part.underline:
            color = PDFColor(part.state.color, True)
            stroke_width = part.state.size * 0.07
            y_u = round(y + part.state.rise - stroke_width, 3)

            if color != self.last_color:
                self.last_color = color
                graphics += ' ' + str(self.last_color)

            if stroke_width != self.last_stroke_width:
                self.last_stroke_width = stroke_width
                graphics += ' {} w'.format(round(self.last_stroke_width, 3))

            graphics += ' {} {} m {} {} l S'.format(
                round(x, 3), y_u, round(x + part_width, 3), y_u
            )

        return graphics

class PDFText(PDFTextBase):
    """Class that represents a rich text paragraph to be added to a
    :class:`pdfme.pdf.PDF` instance.

    ``content`` argument should be a dict, with a key starting with a dot, like
    ``'.b;s:10;c:1;u'`` for example (keep reading to learn more about the format
    of this key), which we are going to refer to as the "the dot key" from here
    on. The value for the dot key is a list/tuple containing strings or more
    ``content`` dicts like the one we are describing here (you can have nested
    ``content`` dicts or what we call a paragraph part), but for simplicity,
    you can pass a string (for non-rich text) or a tuple/list with strings and
    more paragraph parts:

    * If ``content`` argument is a string, it will become the following:

      .. code-block:: python

          { '.': [ <STRING>, ] }

    * If ``content`` argument is a list/tuple, it will become the following:

      .. code-block:: python

          { '.': <LIST_OR_TUPLE> }

    This is an example of a ``content`` argument:

    .. code-block:: python

        {
            ".b;u;i;c:1;bg:0.5;f:Courier": [
                "First part of the paragraph ",
                {
                    ".b:0;u:0;i:0;c:0;bg:": [
                        "and here the second, nested inside the root paragraph,",
                    ]
                },
                "and yet one more part before a ",
                {".c:blue;u:1": "url link", "uri": "https://some.url.com"}
            ]
        }

    This class is a subclass of :class:`pdfme.text.PDFTextBase` and adds the
    logic to let the user of this class pass content in a nested cascading
    "jsonish" format (like HTML), i.e. if you pass a dict to ``content``,
    and this dict has a ``style`` key, all of its children will inherit this
    style and will be able to overwrite some or all of the style parameters
    coming from it. The children will be able to pass their own
    style parameters to their children too, and so on.

    Additional to the dot key, paragraph parts can have the following keys:

    * ``'label'``: this is a string with a unique name (there should be
      only one label with this name in the whole document) representing
      a destination that can be referenced in other parts of the
      document. This is suited for titles, figures, tables, etc.

    * ``'ref'``: this is a string with the name of a label, that will
      become a link to the position of the label referenced.

    * ``'uri'``: this is a string with a reference to a web resource,
      that will turn this text part in a link to that web page.

    * ``'outline'``: an outline is a label that is shown in the outlines panel
      of the PDF reader. This outlines show the structure of the document.
      This attribute is a dict with the following optional keys:
      
      * ``level``: an optional int with the level of this outline in the
        outlines tree. The default value is 1.
        
      * ``text``: an optional string to be shown in the outlines panel for this
        outline. The default value is the contents of this part.

    * ``'ids'``: when method ``run`` is called, dict attr ``result`` is
      available with information to add the paragraph to the PDF, and
      within that information you'll find a key ``ids``, a dict with
      the position and size of the rectangle for each of the ids you
      include in this argument. This way you can "tag" a part of a
      paragraph, call ``run``, and get the position of it afterwards.

    * ``'var'``: this is a string with the name of a global variable,
      previously set in the containing :class:`pdfme.pdf.PDF`
      instance, by adding a new key to its dict attribute ``context``.
      This way you can reuse a repetitive string throughout the PDF
      document.

    Style of the paragraph dicts can be defined in the dot key
    itself (a string with a semi-colon separeted list of the attributes,
    explained in :func:`pdfme.utils.parse_style_str`) or in a ``style`` dict
    too. The attributes for a paragraph style are the following:

    * ``'b'`` (bool) to make text inside this part bold. Default is False.

    * ``'i'`` (bool) to make text inside this part cursive (italics,
      oblique). Default is False.

    * ``'s'`` (int, float) to set the size of the text inside this
      part. Default is 11.

    * ``'f'`` (str) to set the font family of the text inside this
      part. Default is ``'Helvetica'``.

    * ``'u'`` (bool) to make the text inside this part underlined.
      Default is False.

    * ``'c'`` (int, float, list, tuple, str) to set the color of
      the text inside this part. See :func:`pdfme.color.parse_color`
      for information about this attribute. Default is black.

    * ``'bg'`` (int, float, list, tuple, str) to set the background
      color of the text inside this part. See
      :func:`pdfme.color.parse_color` for information about this
      attribute. Default is None.

    * ``'r'`` (int, float) to set the baseline of the text, relative
      to the normal baseline. This is a fraction of the current size of
      the text, i.e. it will move the baseline the text size times this
      number in points, upwards if positive, and downwards if negative.
      Default is 0.

    One more example of a ``content`` argument with a ``style`` dict, and
    additional keys:

    .. code-block:: python

        {
            '.': ['text to be displayed'],
            'style': {
                'b': True,
                'i': True,
                'u': True,
                's': 10.2,
                'f': 'Courier',
                'c': 0.9,
                'bg': 'red',
                'r': 0.5
            },
            'label': 'a_important_paragraph',
            'uri': 'https://github.com/aFelipeSP/pdfme'
        }

    With arguments ``list_text``, ``list_indent`` and ``list_style`` you can
    turn a paragraph into a list paragraph, one that has a bullet or a number
    at the left of the paragraph, with an additional indentation. With this
    you can build a bulleted or numbered list of paragraphs.

    Args:
        content (str, list, tuple, dict): the one just described.
        width (int, float): The width of the paragraph.
        height (int, float): The height of the paragraph.
        x (int, float, optional): The x coordinate of the paragraph.
        y (int, float, optional): The y coordinate of the paragraph
        fonts (PDFFonts, optional): To extract information about the fonts
            being used in the paragraph.
        text_align (str, optional): ``'l'`` for left (default), ``'c'`` for
            center, ``'r'`` for right and ``'j'`` for justified text.
        line_height (int, float, optional): How much space between the
            lines of the paragraph. This is a fraction of each line's
            height, so the real distance between lines can vary depending on
            the text size of each part of the paragraph.
        indent (int, float, optional): The indentation of the first line of
            the paragraph.
        list_text (str, optional): Needed if you want to turn this paragraph
            into a list paragraph. This text will be displayed before the
            paragraph and will be aligned with the first line.
        list_indent (int, float, optional): Needed if you want to turn this
            paragraph into a list paragraph. The space between the start of
            the left side of the rectangle and the left side of the
            paragraph itself. If omitted, this space will be the width of
            the ``list_text``.
        list_style (dict, optional): Needed if you want to turn this
            paragraph into a list paragraph. The style of ``list_text``.
            If omitted, the style of the first part of the first line will
            be used.
        pdf (PDF, optional): To grab global information of the PDF being
            used.
    """
    def __init__(
        self, content: ContentType, width: Number, height: Number,
        x: Number=0, y: Number=0, fonts: 'PDFFonts'=None, text_align: str=None,
        line_height: Number=None, indent: Number=0, list_text: str=None,
        list_indent: Number=None, list_style: dict=None, pdf: 'PDF'=None
    ) -> None:
        self.pdf = pdf
        self.fonts = fonts
        self.content = []
        self._recursive_content_parse(content, TEXT_DEFAULTS, [])
        super().__init__(
            self.content, width, height, x, y, fonts, text_align, line_height,
            indent, list_text, list_indent, list_style, pdf
        )

    def _new_text_part(
        self, style: dict, ids: list, part_var: str=None, last_part: dict=None
    ) -> dict:
        """Creates a new text part compatible with
        :class:`pdfme.text.PDFTextBase`.

        Args:
            style (dict): The style of this new part.
            ids (list): The ids of this new part.
            part_var (str, optional): The name of the 'var' (None if there's no
                var for this part).
            last_part (dict, optional): the part before the one that is going to
                be created with this function.

        Returns:
            dict: representing a part compatible with
                :class:`pdfme.text.PDFTextBase`.
        """
        if last_part is not None and last_part['text'] == '':
            self.content.remove(last_part)
        text_part = {'style': style, 'text': '', 'ids': ids}
        if part_var is not None:
            text_part['var'] = part_var
        self.content.append(text_part)
        return text_part

    def _recursive_content_parse(
        self, content: ContentType, parent_style: dict, ids: list
    ) -> None:
        """Function to be called recursively by this class, to transform the
        content passed to this instance into a list of parts compatible with
        :class:`pdfme.text.PDFTextBase`.

        Args:
            content (str, list, tuple, dict): An object like the one explained
                in the documentation of this class.
            parent_style (dict): A dict with the style of the parent of the
                current part being parsed.
            ids (list): A list of the ids of the parent of the current part
                being parsed.

        Raises:
            TypeError: If the content part passed doesn't have the format
                described in the documentation of this class.
        """
        style = parent_style.copy()
        ids = ids.copy()

        if isinstance(content, str):
            content = {'.': [content]}
        elif isinstance(content, (list, tuple)):
            content = {'.': content}

        if not isinstance(content, dict):
            raise TypeError(
                'content must be of type dict, str, list or tuple: {}'
                .format(content)
            )

        elements = []
        for key, value in content.items():
            if key.startswith('.'):
                style.update(parse_style_str(key[1:], self.fonts))
                if isinstance(value, (int, float)):
                    value = [str(value)]
                elif isinstance(value, str):
                    value = [value]
                if not isinstance(value, (list, tuple)):
                    raise TypeError(
                        'value of . attr must be of type str, list or tuple: {}'
                        .format(value)
                    )
                elements = value
                break

        style.update(process_style(content.get('style'), self.pdf))
        part_var = content.get('var')
        text_part = self._new_text_part(style, ids, part_var)
        text_part['ids'].extend(content.get('ids', []))

        if part_var is not None:
            elements = ['0']

        label = content.get('label')
        if label is not None:
            text_part['ids'].append('$label:' + label)
        ref = content.get('ref')
        if ref is not None:
            text_part['ids'].append('$ref:' + ref)
        uri = content.get('uri')
        if uri is not None:
            text_part['ids'].append('$uri:' + uri)
        outline = content.get('outline')
        if isinstance(outline, dict):
            text = outline.get('text', ''.join(str(e) for e in elements))
            level = outline.get('level', 1)
            if label is None:
                outline_label = str(uuid4())
                text_part['ids'].append('$label:' + outline_label)
            else:
                outline_label = label
            outline_ = {'text': text, 'level': level, 'label': outline_label}
            text_part['ids'].append('$outline:{}'.format(json.dumps(outline_)))

        is_last_string = False

        for element in elements:
            if isinstance(element, (int, float)):
                element = str(element)
            if isinstance(element, str):
                if element == '':
                    continue
                lines = element.split('\n')
                if not is_last_string:
                    text_part = self._new_text_part(
                        style, text_part['ids'], part_var, text_part
                    )
                text_part['text'] += lines[0]
                for line in lines[1:]:
                    self.content.append({'type': 'br'})
                    text_part = self._new_text_part(
                        style, text_part['ids'], part_var, text_part
                    )
                    text_part['text'] += line
                is_last_string = True
            elif isinstance(element, dict):
                self._recursive_content_parse(element, style, text_part['ids'])
                is_last_string = False
            else:
                raise TypeError(
                    'elements must be of type str or dict: {}'.format(element)
                )

        if text_part is not None and text_part['text'] == '':
            self.content.remove(text_part)

from .color import PDFColor
from .fonts import PDFFonts
from .pdf import PDF
from .utils import get_paragraph_stream, parse_style_str, process_style, copy
