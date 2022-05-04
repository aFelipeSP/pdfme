from typing import Iterable, Optional, Union

PARAGRAPH_PROPS = (
    'text_align', 'line_height', 'indent', 'list_text',
    'list_style', 'list_indent'
)

TABLE_PROPS = ('widths', 'borders', 'fills')


Number = Union[int, float]
CellType = Union[dict, str, list, tuple]

class PDFTable:
    """Class that represents a PDF table.

    The ``content`` argument is an iterable representing the rows of the table,
    and each row should be an iterable too, representing each of
    the columns in the row. The elements on a row iterable could be any of the
    elements that you pass to argument ``content`` list in class
    :class:`pdfme.content.PDFContent`. Because of this you can add paragraphs,
    images and content boxes into a table cell.

    Argument ``widths``, if passed, should be an iterable with the width of
    each column in the table. If not passed, all the columns will have the same
    width.

    Argument ``style``, if passed, should be a dict with any of the following
    keys:

    * ``cell_margin``: the margin of the four sides of the cells in the table.
      Default value is ``5``.

    * ``cell_margin_left``: left margin of the cells in the table.
      Default value is ``cell_margin``.

    * ``cell_margin_top``: top margin of the cells in the table.
      Default value is ``cell_margin``.

    * ``cell_margin_right``: right margin of the cells in the table.
      Default value is ``cell_margin``.

    * ``cell_margin_bottom``: bottom margin of the cells in the table.
      Default value is ``cell_margin``.

    * ``cell_fill``: the color of all the cells in the table. Default value is
      ``None`` (transparent). See :func:`pdfme.color.parse_color` for information
      about this attribute.

    * ``border_width``: the width of all the borders in the table. Default value
      is ``0.5``.

    * ``border_color``: the color of all the borders in the table .Default value
      is ``'black'``. See :func:`pdfme.color.parse_color` for information
      about this attribute.

    * ``border_style``: the style of all the borders in the table. It can be
      ``solid``, ``dotted`` or ``solid``. Default value is ``solid``.

    You can overwrite the default values for the cell fills and the borders with
    ``fills`` and ``borders`` arguments.
    These arguments, if passed, should be iterables of dicts. Each dict should
    have a ``pos`` key that contains a string with information of the vertical
    (rows) and horizontal (columns) position of the fills or borders you want
    to change, and for this, such a string should has 2 parts separated by a
    semi colon, the first one for the vertical position and the second one for
    the horizontal position.
    The position can be a single int, a comma-separated list of ints, or a slice
    (range), like the one you pass to get a slice of a python list. For borders
    you have to include a ``h`` or a ``v`` before the positions, to tell if you
    want to change vertical or horizontal borders. The indexes in this string
    can be negative, referring to positions from the end to the beginning.

    The following are examples of valid ``pos`` strings:

    * ``'h0,1,-1;:'`` to modify the first, second and last horizontal lines in
      the table. The horizontal position is a single colon, and thus the whole
      horizontal lines are affected.

    * ``'::2;:'`` to modify all of the fills horizontally, every two rows. This
      would set the current fill to all the cells in the first row, the third
      row, the fifth row and so on.

    Additional to the ``pos`` key for dicts inside ``fills`` iterable, you
    have to include a ``color`` key, with a valid color value. See
    :func:`pdfme.color.parse_color` for information about this attribute.

    Additional to the ``pos`` key for dicts inside ``borders`` iterable, you
    can include ``width`` (border width), ``color`` (border color) and
    ``style`` (border style) keys.

    If a cell element is a dict it's ``style`` dict can have any of the
    following keys: ``cell_margin``, ``cell_margin_left``, ``cell_margin_top``,
    ``cell_margin_right``, ``cell_margin_bottom`` and ``cell_fill``, to overwrite
    the default value of any of these parameters on its cell.
    In a cell dict, you can also include ``colspan`` and ``rowspan`` keys, to
    span it horizontally and vertically respectively. The cells being merged to
    this spanned cell should be None.

    Here's an example of a valid ``content`` value:

    .. code-block:: python

        [
            ['row 1, col 1', 'row 1, col 2', 'row 1, col 3'],
            [
                'row2 col1',
                {
                    'style': {'cell_margin': 10, }
                    'colspan': 2, 'rowspan': 2
                    '.': 'rows 2 to 3, cols 2 to 3',
                },
                None
            ],
            ['row 3, col 1', None, None],
        ]

    Use method :meth:`pdfme.table.PDFTable.run` to add as many rows as possible
    to the rectangle defined by ``x``, ``y```, ``width`` and ``height``.
    The rows are added to this rectangle, until
    they are all inside of it, or until all of the vertical space is used and
    the rest of the rows can not be added. In these two cases method ``run``
    finishes,  and the property ``finished`` will be True if all the elements
    were added, and False if the vertical space ran out.
    If ``finished`` is False, you can set a new rectangle (on a new page for
    example) and use method ``run`` again (passing the parameters of the new
    rectangle) to add the remaining elements that couldn't be added in
    the last rectangle. You can keep doing this until all of the elements are
    added and therefore property ``finished`` is True.

    By using this method the rows are not really added to the PDF object.
    After calling ``run``, the properties ``fills`` and ``lines`` will be
    populated with the fills and lines of the tables that fitted inside the
    rectangle, and ``parts`` will be filled with the paragraphs and images that
    fitted inside the table rectangle too, and you have to add them by yourself
    to the PDF object before using method ``run`` again (in case ``finished`` is
    False), because they will be redefined for the next rectangle after calling
    it again. You can check the ``table`` method in `PDF`_ module to see how
    this process is done.

    Args:
        content (iterable): like the one just explained.
        fonts (PDFFonts): a PDFFonts object used to build paragraphs.
        x (int, float): the x position of the left of the table.
        y (int, float): the y position of the top of the table.
        width (int, float): the width of the table.
        height (int, float): the height of the table.
        widths (Iterable, optional): the widths of each column.
        style (Union[dict, str], optional): the default style of the table.
        borders (Iterable, optional): borders of the table.
        fills (Iterable, optional): fills of the table.
        pdf (PDF, optional): A PDF object used to get string styles inside the
            elements.

    .. _PDF: https://github.com/aFelipeSP/pdfme/blob/main/pdfme/pdf.py
    """
    def __init__(
        self, content: Iterable, fonts: 'PDFFonts', x: Number, y: Number,
        width: Number, height: Number, widths: Iterable=None,
        style: Union[dict, str]=None, borders: Iterable=None,
        fills: Iterable=None, pdf: 'PDF'=None
    ):
        if not isinstance(content, (list, tuple)):
            raise Exception('content must be a list or tuple')

        self.setup(x, y, width, height)
        self.content = content
        self.current_index = 0
        self.fonts = fonts
        self.pdf = pdf
        self.finished = False
        if len(content) == 0 or len(content[0]) == 0:
            return

        self.cols_count = len(content[0])
        self.delayed = {}

        if widths is not None:
            if not isinstance(widths, (list, tuple)):
                raise Exception('widths must be a list or tuple')
            if len(widths) != self.cols_count:
                raise Exception('widths count must be equal to cols count')
            try:
                widths_sum = sum(widths)
                self.widths = [w/widths_sum for w in widths]
            except TypeError:
                raise Exception('widths must be numbers')
            except ZeroDivisionError:
                raise Exception('sum of widths must be greater than zero')
        else:
            self.widths = [1 / self.cols_count] * self.cols_count

        self.style = {'cell_margin': 5, 'cell_fill': None}
        self.style.update(process_style(style, self.pdf))
        self.set_default_border()
        self.setup_borders([] if borders is None else borders)
        self.setup_fills([] if fills is None else fills)
        self.first_row = True

    def setup(
        self, x: Number=None, y: Number=None,
        width: Number=None, height: Number=None
    ) -> None:
        """Method to change the size and position of the table.

        Args:
            x (int, float, optional): the x position of the left of the table.
            y (int, float, optional): the y position of the top of the table.
            width (int, float, optional): the width of the table.
            height (int, float, optional): the height of the table.
        """
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

    def get_state(self) -> dict:
        """Method to get the current state of this table. This can be used
        later in method :meth:`pdfme.table.PDFTable.set_state` to
        restore this state in this table (like a checkpoint in a
        videogame).

        Returns:
            dict: a dict with the state of this table.
        """
        return {
            'current_index': self.current_index, 'delayed': copy(self.delayed)
        }

    def set_state(self, current_index: int=None, delayed: dict=None) -> None:
        """Method to set the state of this table.
        
        The arguments of this method define the current state of this table,
        and with this method you can change that state.

        Args:
            current_index (int, optional): the index of the current row being
                added.
            delayed (dict, optional): a dict with delayed cells that should be
                added before the next row.
        """
        if current_index is not None:
            self.current_index = current_index
        elif delayed is not None:
            self.delayed = delayed

    def set_default_border(self) -> None:
        """Method to create attribute ``default_border`` containing the default
        border values.
        """
        self.default_border = {}
        self.default_border['width'] = self.style.pop('border_width', 0.5)
        color = self.style.pop('border_color', 0)
        self.default_border['color'] = PDFColor(color, True)
        self.default_border['style'] = self.style.pop('border_style', 'solid')

    def parse_pos_string(self, pos: str, counts: int):
        """Method to convert a position string like the ones used in
        ``borders`` and ``fills`` arguments of this class, into a generator
        of positions obtained from this string.

        For more information, see the definition of this class.

        Args:
            pos (str): position string.
            counts (int): the amount of columns or rows.

        Yields:
            tuple: the horizontal and vertical index of each position obtained
            from the ``pos`` string.
        """
        range_strs = pos.split(';')
        if len(range_strs) == 1:
            range_strs.append(':')
        ranges = [
            self.parse_range_string(range_str, count)
            for range_str, count in zip(range_strs, counts)
        ]
        for i in ranges[0]:
            for j in ranges[1]:
                yield i, j

    def parse_range_string(self, data: str, count: int) -> Iterable:
        """Method to convert one of the parts of a position string like the ones
        used in ``borders`` and ``fills`` arguments of this class, into a
        iterator with all the positions obtained from this string.

        For more information, see the definition of this class.

        Args:
            data (str): one of the parts of a position string.
            counts (int): the amount of columns or rows.

        Returns:
            iterable: a list of indexes, or a ``range`` object.
        """
        data = ':' if data == '' else data
        if ':' in data:
            parts = data.split(':')
            num = 0 if parts[0].strip() == '' else int(parts[0])
            parts[0] = num if num >= 0 else count + num
            if len(parts) > 1:
                num = count if parts[1].strip() == '' else int(parts[1])
                parts[1] = num if num >= 0 else count + num
            if len(parts) > 2:
                parts[2] = 1 if parts[2].strip() == '' else int(parts[2])
            return range(*parts)
        else:
            return [
                count + int(i) if int(i) < 0 else int(i)
                for i in data.split(',')
            ]

    def setup_borders(self, borders: Iterable) -> None:
        """Method to process the ``borders`` argument passed to this class, and
        populate attributes ``borders_h`` and ``borders_v``.

        Args:
            borders (iterable): the ``borders`` argument passed to this class.
        """
        rows = len(self.content)
        cols = self.cols_count
        self.borders_h = {}
        self.borders_v = {}
        for b in borders:
            border = copy(self.default_border)
            border.update(b)
            border['color'] = PDFColor(border['color'], True)
            pos = border.pop('pos', None)
            if pos is None:
                continue
            is_vert = pos[0].lower() == 'v'
            counts = (rows, cols + 1) if is_vert else (rows + 1, cols)
            border_l = self.borders_v if is_vert else self.borders_h
            for i, j in self.parse_pos_string(pos[1:], counts):
                first = border_l.setdefault(i, {})
                first[j] = border

    def get_border(self, i: int, j: int, is_vert: bool) -> dict:
        """Method to get the border in the horizontal position ``i``, and
        vertical position ``j``. It takes a vertical border if ``is_vert`` is
        ``true``, and a horizontal border if ``is_vert`` is ``false``
        Args:
            i (int): horizontal position.
            j (int): vertical position.
            is_vert (bool): vertical (True) or horizontal (False) border.

        Returns:
            dict: dict with description of the border in position ``i``, ``j``.
        """
        border_l = self.borders_v if is_vert else self.borders_h
        if i in border_l and j in border_l[i]:
            return copy(border_l[i][j])
        else:
            return copy(self.default_border)

    def setup_fills(self, fills: Iterable) -> None:
        """Method to process the ``fills`` argument passed to this class, and
        populate attribute ``fills_defs``.

        Args:
            fills (iterable): the ``fills`` argument passed to this class.
        """
        v_count = len(self.content)
        h_count = self.cols_count
        self.fills_defs = {}
        for f in fills:
            fill = f['color']
            pos = f.get('pos', None)
            if pos is None:
                continue
            for i, j in self.parse_pos_string(pos, (v_count, h_count)):
                first = self.fills_defs.setdefault(i, {})
                first[j] = fill

    def compare_borders(self, a: dict, b: dict) -> bool:
        """Method that compares border dicts ``a`` and ``b`` and returns if they
        are equal (``True``) or not (``False``)

        Args:
            a (dict): first border.
            b (dict): second border.

        Returns:
            bool: if ``a`` and ``b`` are equal (``True``) or not (``False``).
        """
        return all(a[attr] == b[attr] for attr in ['width', 'color', 'style'])

    def process_borders(
        self, col: int, border_left: dict, border_top: dict
    ) -> None:
        """Method to setup the top and left borders of each cell

        Args:
            col (int): the columns number.
            border_left (dict): the left border dict.
            border_top (dict): the top border dict.
        """
        vert_correction = border_top.get('width', 0)/2
        if not self.top_lines_interrupted:
            aux = self.top_lines[-1].get('width', 0)/2
            if aux > vert_correction:
                vert_correction = aux

        v_line = self.vert_lines[col]
        horiz_correction = border_left.get('width', 0)/2
        if not v_line['interrupted']:
            v_line['list'][-1]['y2'] = self.y_abs - vert_correction
            aux = v_line['list'][-1].get('width', 0)/2
            if aux > horiz_correction:
                horiz_correction = aux

        if not self.top_lines_interrupted:
            self.top_lines[-1]['x2'] += horiz_correction

        if border_top.get('width', 0) > 0:
            x2 = self.x_abs + self.widths[col] * self.width
            if (
                not self.top_lines_interrupted and
                self.compare_borders(self.top_lines[-1], border_top)
            ):
                self.top_lines[-1]['x2'] = x2
            else:
                border_top.update(dict(
                    type='line', y1=self.y_abs,
                    y2=self.y_abs, x2=x2, x1=self.x_abs - horiz_correction
                ))
                self.top_lines.append(border_top)
                self.top_lines_interrupted = False
        else:
            self.top_lines_interrupted = True

        if border_left.get('width', 0) > 0:
            if not (
                not v_line['interrupted'] and
                self.compare_borders(v_line['list'][-1], border_left)
            ):
                border_left.update(dict(
                    type='line', x1=self.x_abs,
                    x2=self.x_abs, y1=self.y_abs + vert_correction
                ))
                v_line['list'].append(border_left)
                v_line['interrupted'] = False
        else:
            v_line['interrupted'] = True

    def run(
        self, x: Number=None, y: Number=None,
        width: Number=None, height: Number=None
    ) -> None:
        """Method to add as many rows as possible to the rectangle defined by
        ``x``, ``y```, ``width`` and ``height`` attributes.

        More information about this method in this class definition.

        Args:
            x (int, float, optional): the x position of the left of the table.
            y (int, float, optional): the y position of the top of the table.
            width (int, float, optional): the width of the table.
            height (int, float, optional): the height of the table.
        """

        self.setup(x, y, width, height)
        self.parts = []
        self.lines = []
        self.fills = []
        self.fills_mem = {}
        self.heights_mem = {}
        self.rowspan = {}
        self.vert_lines = [
            {'list': [], 'interrupted': True}
            for i in range(self.cols_count + 1)
        ]
        self.current_height = 0

        can_continue = True
        if len(self.delayed) > 0:
            can_continue = False
            row = [self.delayed.get(i) for i in range(self.cols_count)]
            action = self.add_row(row, True)
            if action == 'continue':
                self.current_index += 1
                can_continue = True

        cancel = False
        if can_continue:
            while self.current_index < len(self.content):
                action = self.add_row(self.content[self.current_index])
                if action == 'cancel':
                    cancel = True
                    break
                elif action == 'continue':
                    self.current_index += 1
                else:
                    break

        if cancel:
            self.parts = []
            self.lines = []
            self.fills = []
            return

        self.top_lines = []
        self.top_lines_interrupted = True
        self.y_abs = self.y - self.current_height
        for col in range(self.cols_count):
            self.x_abs = self.x + sum(self.widths[0:col]) * self.width
            border_top = self.get_border(self.current_index, col, False)
            self.process_borders(col, {}, border_top)

        self.x_abs = self.x + self.width
        self.process_borders(self.cols_count, {}, {})
        self.lines.extend(self.top_lines)
        self.lines.extend(
            line for vert_line in self.vert_lines for line in vert_line['list']
        )

        if self.current_index >= len(self.content) and len(self.delayed) == 0:
            self.finished = True

    def add_row(self, row: Iterable, is_delayed: bool=False) -> str:
        """Method to add a row to this table.

        Args:
            row (iterable): the row iterable.
            is_delayed (bool, optional): whether this row is being added in
                delayed mode (``True``) or not (``False``).

        Returns:
            str: string with the action that should be performed after this row
            is added.
        """
        if not len(row) == self.cols_count:
            error = 'row {} should be of length {}.'
            raise Exception(error.format(self.current_index+1, self.cols_count))

        self.max_height = 0
        self.row_max_height = self.height - self.current_height
        self.colspan = 0
        self.top_lines = []
        self.top_lines_interrupted = True
        self.is_rowspan = False
        self.y_abs = self.y - self.current_height
        for col, element in enumerate(row):
            move_next = self.add_cell(col, element, is_delayed)
            if move_next:
                continue

        if self.first_row:
            self.first_row = False
            if self.max_height == 0:
                return 'cancel'

        ret = True
        if sum(v['colspan'] for v in self.delayed.values()) == self.cols_count:
            ret = False
        for col in self.delayed:
            if not col in self.rowspan:
                ret = False
                break

        self.x_abs = self.x + self.width
        last_border = self.get_border(self.current_index, len(row), True)
        self.process_borders(len(row), last_border, {})

        self.lines.extend(self.top_lines)

        for col in self.heights_mem:
            self.heights_mem[col] -= self.max_height

        for col, fill in list(self.fills_mem.items()):
            fill['height'] += self.max_height
            if not fill.get('add_later', False) or not ret:
                fill['y'] -= fill['height']
                self.fills.append(fill)
                self.fills_mem.pop(col)

        self.current_height += self.max_height

        return 'continue' if ret else 'interrupt'

    def get_cell_dimensions(
        self, col: int, border_left: dict, border_top: dict,
        cell_style: dict, rowspan: int, colspan: int
    ) -> tuple:
        """Method to get the cell dimensions at column ``col``, taking into
        account the cell borders, and the column and row spans.

        Args:
            col (int): the column of the cell.
            border_left (dict): left border dict.
            border_top (dict): top border dict.
            cell_style (dict): cell style dict.
            rowspan (int): the row span.
            colspan (int): the column span.

        Returns:
            tuple: tuple with position ``(x, y)``, size ``(width, height)``,
            and padding ``(left, top)`` for this cell.
        """
        border_right = self.get_border(
            self.current_index, col + colspan + 1, True
        )
        border_bottom = self.get_border(
            self.current_index + rowspan + 1, col, False
        )

        full_width = sum(self.widths[col:col + colspan + 1]) * self.width
        padd_x_left = border_left.get('width', 0) / 2 + \
            cell_style['cell_margin_left']
        padd_x_right = border_right.get('width', 0) / 2 + \
            cell_style['cell_margin_right']
        padd_x = padd_x_left + padd_x_right
        padd_y_top = border_top.get('width', 0) / 2 + \
            cell_style['cell_margin_top']
        padd_y_bottom = border_bottom.get('width', 0) / 2 + \
            cell_style['cell_margin_bottom']
        padd_y = padd_y_top + padd_y_bottom
        x = self.x_abs + padd_x_left
        y = self.y_abs - padd_y_top
        width = full_width - padd_x
        height = self.row_max_height - padd_y
        return x, y, width, height, padd_x, padd_y

    def is_span(
        self, col: int, border_left: dict, border_top: dict, is_delayed: bool
    ) -> bool:
        """Method to check if cell at column ``col`` is part of a spanned cell
        (``True``) or not (``False``).

        Args:
            col (int): the column of the cell.
            border_left (dict): left border dict.
            border_top (dict): top border dict.
            is_delayed (bool, optional): whether this row is being added in
                delayed mode (``True``) or not (``False``).

        Returns:
            bool: whether ``col`` is part of a spanned cell (``True``) or not
            (``False``).
        """
        rowspan_memory = self.rowspan.get(col, None)
        can_continue = False
        if rowspan_memory is None:
            if self.colspan > 0:
                self.colspan -= 1
                border_left['width'] = 0
                if self.is_rowspan:
                    border_top['width'] = 0
                    if self.colspan == 0:
                        self.is_rowspan = False
                can_continue = True
        elif not is_delayed:
            rowspan_memory['rows'] -= 1
            self.colspan = rowspan_memory['cols']
            self.is_rowspan = True
            border_top['width'] = 0

            if rowspan_memory['rows'] == 0:
                self.rowspan.pop(col)
                if col in self.fills_mem:
                    self.fills_mem[col]['add_later'] = False
                if self.heights_mem.get(col, 0) > self.max_height:
                    self.max_height = self.heights_mem[col]
                if self.colspan == 0:
                    self.is_rowspan = False
            can_continue = True
        return can_continue

    def get_cell_style(self, element: CellType) -> tuple:
        """Method to extract the cell style from a cell ``element``.

        Args:
            element (dict, str, list, tuple): the cell element to extract the
                cell style from.

        Returns:
            tuple: tuple with a copy of ``element``, the element ``style``,
            and the ``cell_style``.
        """
        if isinstance(element, dict) and 'delayed' in element:
            cell_style = element['cell_style']
            style = {}
        else:
            style = copy(self.style)

            if element is None:
                element = ''
            if not isinstance(element, (dict, str, list, tuple)):
                element = str(element)
            if isinstance(element, (str, list, tuple)):
                element = {'.': element}

            if not isinstance(element, dict):
                raise TypeError(
                    'Elements must be of type dict, str, list or tuple:'
                    + str(element)
                )

            keys = [key for key in element.keys() if key.startswith('.')]
            if len(keys) > 0:
                style.update(parse_style_str(keys[0][1:], self.fonts))
            style.update(process_style(element.get('style'), self.pdf))
            cell_style = {}
            attr = 'cell_margin'
            for side in ('top', 'right', 'bottom', 'left'):
                cell_style[attr + '_' + side] = style.pop(
                    attr + '_' + side, style.get(attr, None)
                )
            style.pop(attr, None)
            cell_style['cell_fill'] = style.pop('cell_fill', None)
        element = copy(element)
        return element, style, cell_style

    def _setup_cell_fill(
        self, col: int, cell_style: dict, width: Number, rowspan: int
    ) -> None:
        """Method to optionally add the fill color in ``cell`style`` to
        attribute ``fills_mem``

        Args:
            col (int): the cell column index.
            cell_style (dict): the cell style.
            width (Number): the width of the cell.
            rowspan (int): the rowspan of the cell.
        """
        fill_color = cell_style.get('cell_fill', None)

        if fill_color is None:
            fill_color = (
                self.fills_defs.get(self.current_index, {}).get(col, None)
            )

        if fill_color is not None:
            self.fills_mem[col] = { 'type': 'fill', 'x': self.x_abs,
                'y': self.y_abs, 'width': width, 'height': 0,
                'color': PDFColor(fill_color, stroke=False)
            }
            if rowspan > 0:
                self.fills_mem[col]['add_later'] = True

    def _is_delayed_type(self, el: dict, type_: str) -> bool:
        return 'delayed' in el and el['type'] == type_

    def is_type(self, el, type_):
        return type_ in el or self._is_delayed_type(el, type_)

    def add_cell(self, col: int, element: CellType, is_delayed: bool) -> bool:
        """Method to add a cell to the current row.

        Args:
            col (int): the column index for the cell.
            element (dict, str, list, tuple): the cell element to be added.
            is_delayed (bool, optional): whether current row is being added in
                delayed mode (``True``) or not (``False``).

        Returns:
            bool: whether ``col`` is part of a spanned cell (``True``) or not
            (``False``).
        """
        self.x_abs = self.x + sum(self.widths[0:col]) * self.width
        border_left = self.get_border(self.current_index, col, True)
        border_top = self.get_border(self.current_index, col, False)
        can_continue = self.is_span(col, border_left, border_top, is_delayed)
        self.process_borders(col, border_left, border_top)
        if can_continue:
            return True

        element, style, cell_style = self.get_cell_style(element)

        colspan_original = element.get('colspan', 1)
        self.colspan = colspan_original - 1
        row_added = element.get('row', self.current_index)
        rowspan = element.get('rowspan', 1) - 1 - self.current_index + \
            row_added
        if rowspan > 0:
            self.rowspan[col] = {'rows': rowspan, 'cols': self.colspan}

        x, y, width, height, padd_x, padd_y = self.get_cell_dimensions(
            col, border_left, border_top, cell_style, rowspan, self.colspan
        )

        delayed = {
            'cell_style': cell_style, 'colspan': colspan_original,
            'rowspan': element.get('rowspan', 1), 'row': row_added
        }

        self._setup_cell_fill(col, cell_style, width + padd_x, rowspan)

        keys = [key for key in element.keys() if key.startswith('.')]

        real_height = 0
        did_finished = False
        if len(keys) > 0 or self._is_delayed_type(element, 'text'):
            real_height, did_finished = self.process_text(
                element, x, y, width, height, style, delayed
            )
        elif self.is_type(element, 'image'):
            real_height, did_finished = self.process_image(
                element, x, y, width, height, delayed
            )
        elif self.is_type(element, 'content'):
            real_height, did_finished = self.process_content(
                element, x, y, width, height, style, delayed
            )

        elif self.is_type(element, 'table'):
            real_height, did_finished = self.process_table(
                element, x, y, width, height, style, delayed
            )

        if did_finished:
            self.delayed.pop(col, None)
        else:
            self.delayed[col] = delayed

        real_height += padd_y if real_height>0 else (0 if self.first_row else 4)
        if rowspan > 0:
            self.heights_mem[col] = real_height
            real_height = 0
        if real_height > self.max_height:
            self.max_height = real_height

        return False

    def process_text(
        self, element: dict, x: Number, y: Number, width: Number,
        height: Number, style: dict, delayed: dict
    ) -> float:
        """Method to add a paragraph to a cell.

        Args:
            col (int): the column index of the cell.
            element (dict): the paragraph element
            x (Number): the x coordinate of the paragraph.
            y (Number): the y coordinate of the paragraph.
            width (Number): the width of the paragraph.
            height (Number): the height of the paragraph.
            style (dict): the paragraph style.
            delayed (dict): the delayed element to add the current paragraph if
                it can not be added completely to the current cell.

        Returns:
            float: the height of the paragraph.
        """
        if 'delayed' in element:
            pdf_text = element['delayed']
            pdf_text.setup(x, y, width, height)
            pdf_text.set_state(**element['state'])
            pdf_text.finished = False
        else:
            par_style = {
                v: style.get(v) for v in PARAGRAPH_PROPS if v in style
            }
            element['style'] = style
            pdf_text = PDFText(
                element, width, height, x, y, fonts=self.fonts, pdf=self.pdf,
                **par_style
            )

        result = pdf_text.run()
        result['type'] = 'paragraph'
        self.parts.append(result)

        if not pdf_text.finished:
            delayed.update({'delayed': pdf_text, 'type': 'text'})
            delayed['state'] = pdf_text.get_state()
        return pdf_text.current_height, pdf_text.finished

    def process_image(
        self, element: dict, x: Number, y: Number, 
        width: Number, height: Number, delayed: dict
    ) -> float:
        """Method to add an image to a cell.

        Args:
            col (int): the column index of the cell.
            element (dict): the image element
            x (Number): the x coordinate of the image.
            y (Number): the y coordinate of the image.
            width (Number): the width of the image.
            height (Number): the height of the image.
            delayed (dict): the delayed element to add the current image if
                it can not be added to the current cell.

        Returns:
            float: the height of the image.
        """
        if 'delayed' in element:
            pdf_image = element['delayed']
        else:
            pdf_image = PDFImage(
                element['image'], element.get('extension'),
                element.get('image_name')
            )
        img_width = width
        img_height = img_width * pdf_image.height / pdf_image.width

        real_height = 0
        finished = False
        if img_height < height:
            real_height = img_height
            self.parts.append({
                'type': 'image', 'pdf_image': pdf_image,
                'x': x, 'y': y - img_height,
                'width': img_width, 'height': img_height
            })
            finished = True
        else:
            delayed.update({'delayed': pdf_image, 'type': 'image'})
        return real_height, finished

    def process_content(
        self, element: dict, x: Number, y: Number,
        width: Number, height: Number, style: dict, delayed: dict
    ) -> float:
        """Method to add a content box to a cell.

        Args:
            col (int): the column index of the cell.
            element (dict): the content box element
            x (Number): the x coordinate of the content box.
            y (Number): the y coordinate of the content box.
            width (Number): the width of the content box.
            height (Number): the height of the content box.
            style (dict): the content box style.
            delayed (dict): the delayed element to add the current content box
                if it can not be added completely to the current cell.

        Returns:
            float: the height of the content box.
        """
        if 'delayed' in element and element['type'] == 'content':
            pdf_content = element['delayed']
            pdf_content.setup(x, y, width, height)
            pdf_content.set_state(**element['state'])
            pdf_content.finished = False
        else:
            element['style'] = style
            pdf_content = PDFContent(
                element, self.fonts, x, y, width, height, self.pdf
            )

        pdf_content.run()

        self.parts.extend(pdf_content.parts)
        self.lines.extend(pdf_content.lines)
        self.fills.extend(pdf_content.fills)

        if not pdf_content.finished:
            delayed.update({'delayed': pdf_content, 'type': 'content'})
            delayed['state'] = pdf_content.get_state()
        return pdf_content.current_height, pdf_content.finished

    def process_table(
        self, element: dict, x: Number, y: Number,
        width: Number, height: Number, style: dict, delayed: dict
    ) -> float:
        """Method to add a table to a cell.

        Args:
            col (int): the column index of the cell.
            element (dict): the table element
            x (Number): the x coordinate of the table.
            y (Number): the y coordinate of the table.
            width (Number): the width of the table.
            height (Number): the height of the table.
            style (dict): the table style.
            delayed (dict): the delayed element to add the current table if
                it can not be added completely to the current cell.

        Returns:
            float: the height of the table.
        """
        if 'delayed' in element and element['type'] == 'table':
            pdf_table = element['delayed']
            pdf_table.setup(x, y, width, height)
            pdf_table.set_state(**element['state'])
            pdf_table.finished = False
        else:
            table_props = {
                v: element.get(v) for v in TABLE_PROPS if v in element
            }
            pdf_table = PDFTable(
                element['table'], self.fonts, x, y, width, height,
                style=style, pdf=self.pdf, **table_props
            )

        pdf_table.run()

        self.parts.extend(pdf_table.parts)
        self.lines.extend(pdf_table.lines)
        self.fills.extend(pdf_table.fills)

        if not pdf_table.finished:
            delayed.update({'delayed': pdf_table, 'type': 'table'})
            delayed['state'] = pdf_table.get_state()
        return pdf_table.current_height, pdf_table.finished

from .color import PDFColor
from .content import PDFContent
from .fonts import PDFFonts
from .image import PDFImage
from .pdf import PDF
from .text import PDFText
from .utils import parse_style_str, process_style, copy