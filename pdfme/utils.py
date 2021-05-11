import re
from .color import PDFColor

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

def subs(string, *args, **kwargs):
    return string.format(*args, **kwargs).encode('latin')

def get_page_size(size):
    if isinstance(size, int):
        return (size, size)
    elif isinstance(size, str):
        return page_sizes[size]
    elif isinstance(size, (list, tuple)):
        return tuple(size)
    else:
        raise Exception('Page size must be a two numbers list or tuple, a number'
            '(for a square page) or any of the following strings: {}'.format(
                ', '. join('"{}"'.format(name) for name in page_sizes.keys())
            ))

def parse_margin(margin):
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


def parse_style_str(style_str, fonts):
    style = {}
    for attrs_str in style_str.split(';'):
        attrs = attrs_str.split(':')
        if len(attrs) == 0 or attrs == ['']: continue
        elif len(attrs) == 1:
            attr = attrs[0].strip()
            if not attr in ['b', 'i', 'u']:
                raise ValueError('Style elements with no paramter must '
                    'be whether "b" for bold, "i" for italics(Oblique) or '
                    '"u" for underline.')
            style[attr] = True
        elif len(attrs) == 2:
            attr = attrs[0].strip()
            value = attrs[1].strip()
            if attr == "f":
                if value not in fonts:
                    raise ValueError('Style element "f" must have the name '
                        'of a font family already added.')
                
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
                    raise ValueError('Style element value for "s" is wrong:'
                        ' {}'.format(value))
            elif attrs[0] == 'r':
                try: style['r'] = float(value)
                except:
                    raise ValueError('Style element value for "r" is wrong:'
                        ' {}'.format(value))
            else:
                raise ValueError('Style elements with arguments must be "f", '
                    '"s", "c", "r"')

        else:
            raise ValueError('Style elements must be "b", "u", "i", "f", '
                    '"s", "c", "r"')

    return style

def default(value, default_):
    return default_ if value is None else value

def get_char_width(char, size, fonts, font_family, font_mode):
    return size * fonts[font_family][font_mode]['widths'][char] / 1000

def get_word_width(word, size, fonts, font_family, font_mode):
    width = 0
    for char in word:
        width += get_char_width(char, size, fonts, font_family, font_mode)
    return width

def create_graphics(graphics):
    last_fill = last_color = last_line_width = last_line_style = None
    stream = ' q'
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
                line_style = ' 0 J [{} {}] 0'.format(round(g['width']*2, 3),
                    round(g['width'], 3))
            elif g['style'] == 'dotted':
                line_style = ' 1 J [0 {}] {}'.format(round(g['width'], 3),
                    round(g['width'], 3)*0.5)
            else:
                line_style = ' 0 J [] 0'

            if line_style != last_line_style:
                last_line_style = line_style
                stream += line_style

            stream += ' {} {} m {} {} l S'.format(
                round(g['x1'], 3), round(g['y1'], 3),
                round(g['x2'], 3), round(g['y2'], 3),
            )
    return stream + ' Q'