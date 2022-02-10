import re
from typing import Any, Iterable, Union

page_sizes = {
    'a5': (419.528, 595.276),
    'a4': (595.276, 841.89),
    'a3': (841.89, 1190.551),
    'b5': (498.898, 708.661),
    'b4': (708.661, 1000.63),
    'jis-b5': (515.906, 728.504),
    'jis-b4': (728.504, 1031.812),
    'letter': (612, 792),
    'legal': (612, 1008),
    'ledger': (792, 1224)
}

Number = Union[int, float]
MarginType = Union[int, float, Iterable[Number], dict]

def subs(string: str, *args: tuple, **kwargs: dict) -> bytes:
    """Function to take ``string``, format it using ``args`` and ``kwargs`` and
    encode it into bytes.

    Args:
        string (str): string to be transformed.

    Returns:
        bytes: the resulting bytes.
    """
    return string.format(*args, **kwargs).encode('latin')

def process_style(style: Union[str, dict], pdf: 'PDF'=None) -> dict:
    """Function to use a named style from the PDF instance passed, if ``style``
    is a string or ``style`` itself if this is a dict.

    Args:
        style (str, dict): a style name (str) or a style dict.
        pdf (PDF, optional): the PDF to extract the named style from.

    Returns:
        dict: a style dict.
    """
    if style is None:
        return {}
    elif isinstance(style, str):
        if pdf is None:
            return {}
        return copy(pdf.formats[style])
    elif isinstance(style, dict):
        return style
    else:
        raise Exception('style must be a str with the name of a style or dict')

def get_page_size(size: Union[Number, str, Iterable]) -> tuple:
    """Function to get tuple with the width and height of a page, from the value
    in ``size``.

    If ``size`` is a str, it should be the name of a page size: ``a5``, ``a4``,
    ``a3``, ``b5``, ``b4``, ``jis-b5``, ``jis-b4``, ``letter``, ``legal`` and
    ``ledger``.

    If ``size`` is a int, the page will be a square of size ``(int, int)``.

    If ``size`` is a list or tuple, it will be converted to a tuple.

    Args:
        size (int, float, str, iterable): the page size.

    Returns:
        tuple: tuple with the page width and height.
    """
    if isinstance(size, (int, float)):
        return (size, size)
    elif isinstance(size, str):
        return page_sizes[size]
    elif isinstance(size, (list, tuple)):
        return tuple(size)
    else:
        raise Exception('Page size must be a two numbers list or tuple, a'
            'number (for a square page) or any of the following strings: {}'
            .format(
                ', '. join('"{}"'.format(name) for name in page_sizes.keys())
            ))

def parse_margin(margin: MarginType) -> dict:
    """Function to transform ``margin`` into a dict containing keys ``top``,
    ``left``, ``bottom`` and ``right`` with the margins.

    If ``margin`` is a dict, it is returned as it is.

    If ``margin`` is a string, it will be splitted using commas or spaces, and
    each substring will be converted into a number, and after this, the list
    obtained will have the same treatment of an iterable.

    If ``margin`` is an iterable of 1 element, its value will be the margin for
    the four sides. If it has 2 elements, the first one will be the ``top`` and
    ``bottom`` margin, and the second one will be the ``left`` and ``right``
    margin. If it has 3 elements, these will be the ``top``, ``right`` and
    ``bottom`` margins, and the ``left`` margin will be the second number (the
    same as ``right``). If it has 4 elements, they will be the ``top``,
    ``right``, ``bottom`` and ``left`` margins respectively.

    Args:
        margin (str, int, float, tuple, list, dict): the margin element.

    Returns:
        dict: dict containing keys ``top``, ``left``, ``bottom`` and ``right``
        with the margins.
    """
    if isinstance(margin, dict):
        return margin

    if isinstance(margin, str):
        margin = re.split(',| ', margin)
        if len(margin) == 1:
            margin = float(margin)
        else:
            margin = [float(x) for x in margin]

    if isinstance(margin, (int, float)):
        margin = [margin] * 4

    if isinstance(margin, (list, tuple)):
        if len(margin) == 0:
            margin = [0] * 4
        elif len(margin) == 1:
            margin = margin * 4
        elif len(margin) == 2:
            margin = margin * 2
        elif len(margin) == 3:
            margin = margin + [margin[1]]
        elif len(margin) > 4:
            margin = margin[0:4]

        return {k: v for k, v in zip(['top', 'right', 'bottom', 'left'], margin)}
    else:
        raise TypeError('margin property must be of type str, int, list or dict')


def parse_style_str(style_str: str, fonts: 'PDFFonts') -> dict:
    """Function to parse a style string into a style dict.

    It parses a string with a semi-colon separeted list of the style attributes
    you want to apply (for a list of the attributes you can use in this string
    see :class:`pdfme.text.PDFText`). For the ones that are of type bool, you
    just have to include the name and it will mean they are ``True``,
    and for the rest you need to include the name, a colon, and the value of the
    attribute. In case the value is a color, it can be any of the possible
    string inputs to function :func:`pdfme.color.parse_color`.
    Empty values mean ``None``, and ``"1" == True`` and ``"0" == False`` for
    bool attributes.

    This is an example of a valid style string:

    .. code-block::

        ".b;s:10;c:1;u:0;bg:"

    Args:
        style_str (str): The string representing the text style.
        fonts (PDFFonts): If a font family is included, this is needed to check
            if it is among the fonts already added to the PDFFonts instance
            passed.

    Raises:
        ValueError: If the string format is not valid.

    Returns:
        dict: A style dict like the one described in :class:`pdfme.text.PDFText`.
    """

    style = {}
    for attrs_str in style_str.split(';'):
        attrs = attrs_str.split(':')
        if len(attrs) == 1:
            if attrs[0] == '':
                continue
            attr = attrs[0].strip()
            if not attr in ['b', 'i', 'u']:
                raise ValueError(
                    'Style elements with no paramter must be whether "b" for '
                    'bold, "i" for italics(Oblique) or "u" for underline.'
                )
            style[attr] = True
        elif len(attrs) == 2:
            attr = attrs[0].strip()
            value = attrs[1].strip()

            if attr in ['b', 'i', 'u']:
                if value == '1':
                    style[attr] = True
                elif value == '0':
                    style[attr] = False
                else:
                    raise ValueError(
                        'Style element "{}" must be 0 or 1: {}'
                        .format(attr, value)
                    )
            if attr == "f":
                if value not in fonts.fonts:
                    raise ValueError(
                        'Style element "f" must have the name of a font family'
                        ' already added.'
                    )

                style['f'] = value
            elif attr == "c":
                style['c'] = PDFColor(value)
            elif attr == "bg":
                style['bg'] = PDFColor(value)
            elif attrs[0] == "s":
                try:
                    v = float(value)
                    if int(v) == v:
                        v = int(v)
                    style['s'] = v
                except:
                    raise ValueError(
                        'Style element value for "s" is wrong:'
                        ' {}'.format(value)
                    )
            elif attrs[0] == 'r':
                try: style['r'] = float(value)
                except:
                    raise ValueError(
                        'Style element value for "r" is wrong:'
                        ' {}'.format(value)
                    )
            else:
                raise ValueError(
                    'Style elements with arguments must be '
                    '"b", "u", "i", "f", "s", "c", "r"'
                )

        else:
            raise ValueError('Invalid Style string: {}'.format(attrs_str))

    return style

def create_graphics(graphics: list) -> str:
    """Function to transform a list of graphics dicts (with lines and fill
    rectangles) into a PDF stream, ready to be added to a PDF page stream.

    Args:
        graphics (list): list of graphics dicts.

    Returns:
        str: a PDF stream containing the passed graphics.
    """
    last_fill = last_color = last_line_width = last_line_style = None
    stream = ''
    for g in graphics:
        if g['type'] == 'fill':
            if g['color'] != last_fill:
                last_fill = g['color']
                stream += ' ' + str(last_fill)

            stream += ' {} {} {} {} re F'.format(
                round(g['x'], 3), round(g['y'], 3),
                round(g['width'], 3), round(g['height'], 3)
            )

        if g['type'] == 'line':
            if g['color'] != last_color:
                last_color = g['color']
                stream += ' ' + str(last_color)

            if g['width'] != last_line_width:
                last_line_width = g['width']
                stream += ' {} w'.format(round(g['width'], 3))

            if g['style'] == 'dashed':
                line_style = ' 0 J [{} {}] 0 d'.format(round(g['width']*3, 3),
                    round(g['width']*1.5, 3))
            elif g['style'] == 'dotted':
                line_style = ' 1 J [0 {}] {} d'.format(round(g['width']*2, 3),
                    round(g['width'], 3)*0.5)
            elif g['style'] == 'solid':
                line_style = ' 0 J [] 0 d'
            else:
                raise Exception(
                    'line style should be dotted, dashed or solid: {}'
                    .format(g['style'])
                )

            if line_style != last_line_style:
                last_line_style = line_style
                stream += line_style

            stream += ' {} {} m {} {} l S'.format(
                round(g['x1'], 3), round(g['y1'], 3),
                round(g['x2'], 3), round(g['y2'], 3),
            )

    if stream != '':
        stream = ' q' + stream + ' Q'

    return stream

def _roman_five(n, one, five):
    return one * n if n < 4 else (one + five if n == 4 else five)

def _roman_ten(n, one, five, ten):
    return _roman_five(n, one, five) if n < 5 else ((five if n < 9 else '')
        + _roman_five(n - 5, one, ten) if n > 5 else five)

def to_roman(n: int) -> str:
    """Function to transform ``n`` integer into a string with its corresponding
    Roman representation.

    Args:
        n (int): the number to be transformed.

    Returns:
        str: the Roman representation of the integer passed.
    """
    if not (0 < n < 4000):
        raise Exception('0 < n < 4000')
    roman = ''
    n = str(int(n))
    if len(n) > 0:
        roman = _roman_ten(int(n[-1]), 'I', 'V', 'X')
    if len(n) > 1:
        roman = _roman_ten(int(n[-2]), 'X', 'L', 'C') + roman
    if len(n) > 2:
        roman = _roman_ten(int(n[-3]), 'C', 'D', 'M') + roman
    if len(n) > 3:
        roman = _roman_ten(int(n[-4]), 'M', '', '') + roman
    return roman

def get_paragraph_stream(
    x: Number, y: Number, text_stream: str, graphics_stream: str
) -> str:
    """Function to create a paragraph stream, in position ``x`` and ``y``, using
    stream information in ``text_stream`` and ``graphics_stream``.

    Args:
        x (int, float): the x coordinate of the paragraph.
        y (int, float): the y coordinate of the paragraph.
        text_stream (str): the text stream of the paragraph.
        graphics_stream (str): the graphics stream of the paragraph.

    Returns:
        str: the whole stream of the paragraph.
    """

    stream = ''
    x, y = round(x, 3), round(y, 3)
    if graphics_stream != '':
        stream += ' q 1 0 0 1 {} {} cm{} Q'.format(x, y, graphics_stream)
    if text_stream != '':
        stream += ' BT 1 0 0 1 {} {} Tm{} ET'.format(x, y, text_stream)
    return stream

def copy(obj: Any) -> Any:
    """Function to copy objects like the ones used in this project: dicts,
    lists, PDFText, PDFTable, PDFContent, etc.


    Args:
        obj (Any): the object to be copied.

    Returns:
        Any: the copy of the object passed as argument.
    """
    if isinstance(obj, list):
        return [copy(el) for el in obj]
    elif isinstance(obj, dict):
        return {k: copy(v) for k, v in obj.items()}
    else:
        return obj

def parse_range_string(range_str: str) -> set:
    """Function to convert a string of comma-separated integers and integer 
    ranges into a set of all the integers included in those.

    Args:
        range_str (str): comma-separated list of integers and integer 
            ranges.

    Returns:
        set: a set of integers.
    """
    integers_set = set()
    for part in range_str.split(','):
        range_parts = part.split(':')
        if len(range_parts) == 1:
            integers_set.add(int(range_parts[0].strip()))
        else:
            first = range_parts[0].strip()
            range_parts[0] = 0 if first == '' else int(first)
            if len(range_parts) > 1:
                range_parts[1] = int(range_parts[1].strip())
            if len(range_parts) > 2:
                range_parts[2] = int(range_parts[2].strip())
            integers_set.update(range(*range_parts))

    return integers_set

from .color import PDFColor
from .fonts import PDFFonts
from .pdf import PDF
