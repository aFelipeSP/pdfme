import re
from typing import Union

colors = {
    'aliceblue': [0.941, 0.973, 1.0],
    'antiquewhite': [0.98, 0.922, 0.844],
    'aqua': [0, 1.0, 1.0],
    'aquamarine': [0.5, 1.0, 0.832],
    'azure': [0.941, 1.0, 1.0],
    'beige': [0.961, 0.961, 0.863],
    'bisque': [1.0, 0.895, 0.77],
    'black': [0, 0, 0],
    'blanchedalmond': [1.0, 0.922, 0.805],
    'blue': [0, 0, 1.0],
    'blueviolet': [0.543, 0.172, 0.887],
    'brown': [0.648, 0.168, 0.168],
    'burlywood': [0.871, 0.723, 0.531],
    'cadetblue': [0.375, 0.621, 0.629],
    'chartreuse': [0.5, 1.0, 0],
    'chocolate': [0.824, 0.414, 0.121],
    'coral': [1.0, 0.5, 0.316],
    'cornflowerblue': [0.395, 0.586, 0.93],
    'cornsilk': [1.0, 0.973, 0.863],
    'crimson': [0.863, 0.082, 0.238],
    'cyan': [0, 1.0, 1.0],
    'darkblue': [0, 0, 0.547],
    'darkcyan': [0, 0.547, 0.547],
    'darkgoldenrod': [0.723, 0.527, 0.047],
    'darkgray': [0.664, 0.664, 0.664],
    'darkgrey': [0.664, 0.664, 0.664],
    'darkgreen': [0, 0.395, 0],
    'darkkhaki': [0.742, 0.719, 0.422],
    'darkmagenta': [0.547, 0, 0.547],
    'darkolivegreen': [0.336, 0.422, 0.188],
    'darkorange': [1.0, 0.551, 0],
    'darkorchid': [0.602, 0.199, 0.801],
    'darkred': [0.547, 0, 0],
    'darksalmon': [0.914, 0.59, 0.48],
    'darkseagreen': [0.562, 0.738, 0.562],
    'darkslateblue': [0.285, 0.242, 0.547],
    'darkslategray': [0.188, 0.312, 0.312],
    'darkslategrey': [0.188, 0.312, 0.312],
    'darkturquoise': [0, 0.809, 0.82],
    'darkviolet': [0.582, 0, 0.828],
    'deeppink': [1.0, 0.082, 0.578],
    'deepskyblue': [0, 0.75, 1.0],
    'dimgray': [0.414, 0.414, 0.414],
    'dimgrey': [0.414, 0.414, 0.414],
    'dodgerblue': [0.121, 0.566, 1.0],
    'firebrick': [0.699, 0.137, 0.137],
    'floralwhite': [1.0, 0.98, 0.941],
    'forestgreen': [0.137, 0.547, 0.137],
    'fuchsia': [1.0, 0, 1.0],
    'gainsboro': [0.863, 0.863, 0.863],
    'ghostwhite': [0.973, 0.973, 1.0],
    'gold': [1.0, 0.844, 0],
    'goldenrod': [0.855, 0.648, 0.129],
    'gray': [0.504, 0.504, 0.504],
    'grey': [0.504, 0.504, 0.504],
    'green': [0, 0.504, 0],
    'greenyellow': [0.68, 1.0, 0.188],
    'honeydew': [0.941, 1.0, 0.941],
    'hotpink': [1.0, 0.414, 0.707],
    'indianred': [0.805, 0.363, 0.363],
    'indigo': [0.297, 0, 0.512],
    'ivory': [1.0, 1.0, 0.941],
    'khaki': [0.941, 0.902, 0.551],
    'lavender': [0.902, 0.902, 0.98],
    'lavenderblush': [1.0, 0.941, 0.961],
    'lawngreen': [0.488, 0.988, 0],
    'lemonchiffon': [1.0, 0.98, 0.805],
    'lightblue': [0.68, 0.848, 0.902],
    'lightcoral': [0.941, 0.504, 0.504],
    'lightcyan': [0.879, 1.0, 1.0],
    'lightgoldenrodyellow': [0.98, 0.98, 0.824],
    'lightgray': [0.828, 0.828, 0.828],
    'lightgrey': [0.828, 0.828, 0.828],
    'lightgreen': [0.566, 0.934, 0.566],
    'lightpink': [1.0, 0.715, 0.758],
    'lightsalmon': [1.0, 0.629, 0.48],
    'lightseagreen': [0.129, 0.699, 0.668],
    'lightskyblue': [0.531, 0.809, 0.98],
    'lightslategray': [0.469, 0.535, 0.602],
    'lightslategrey': [0.469, 0.535, 0.602],
    'lightsteelblue': [0.691, 0.77, 0.871],
    'lightyellow': [1.0, 1.0, 0.879],
    'lime': [0, 1.0, 0],
    'limegreen': [0.199, 0.805, 0.199],
    'linen': [0.98, 0.941, 0.902],
    'magenta': [1.0, 0, 1.0],
    'maroon': [0.504, 0, 0],
    'mediumaquamarine': [0.402, 0.805, 0.668],
    'mediumblue': [0, 0, 0.805],
    'mediumorchid': [0.73, 0.336, 0.828],
    'mediumpurple': [0.578, 0.441, 0.859],
    'mediumseagreen': [0.238, 0.703, 0.445],
    'mediumslateblue': [0.484, 0.41, 0.934],
    'mediumspringgreen': [0, 0.98, 0.605],
    'mediumturquoise': [0.285, 0.82, 0.801],
    'mediumvioletred': [0.781, 0.086, 0.523],
    'midnightblue': [0.102, 0.102, 0.441],
    'mintcream': [0.961, 1.0, 0.98],
    'mistyrose': [1.0, 0.895, 0.883],
    'moccasin': [1.0, 0.895, 0.711],
    'navajowhite': [1.0, 0.871, 0.68],
    'navy': [0, 0, 0.504],
    'oldlace': [0.992, 0.961, 0.902],
    'olive': [0.504, 0.504, 0],
    'olivedrab': [0.422, 0.559, 0.141],
    'orange': [1.0, 0.648, 0],
    'orangered': [1.0, 0.273, 0],
    'orchid': [0.855, 0.441, 0.84],
    'palegoldenrod': [0.934, 0.91, 0.668],
    'palegreen': [0.598, 0.984, 0.598],
    'paleturquoise': [0.688, 0.934, 0.934],
    'palevioletred': [0.859, 0.441, 0.578],
    'papayawhip': [1.0, 0.938, 0.836],
    'peachpuff': [1.0, 0.855, 0.727],
    'peru': [0.805, 0.523, 0.25],
    'pink': [1.0, 0.754, 0.797],
    'plum': [0.867, 0.629, 0.867],
    'powderblue': [0.691, 0.879, 0.902],
    'purple': [0.504, 0, 0.504],
    'rebeccapurple': [0.402, 0.203, 0.602],
    'red': [1.0, 0, 0],
    'rosybrown': [0.738, 0.562, 0.562],
    'royalblue': [0.258, 0.414, 0.883],
    'saddlebrown': [0.547, 0.273, 0.078],
    'salmon': [0.98, 0.504, 0.449],
    'sandybrown': [0.957, 0.645, 0.379],
    'seagreen': [0.184, 0.547, 0.344],
    'seashell': [1.0, 0.961, 0.934],
    'sienna': [0.629, 0.324, 0.18],
    'silver': [0.754, 0.754, 0.754],
    'skyblue': [0.531, 0.809, 0.922],
    'slateblue': [0.418, 0.355, 0.805],
    'slategray': [0.441, 0.504, 0.566],
    'slategrey': [0.441, 0.504, 0.566],
    'snow': [1.0, 0.98, 0.98],
    'springgreen': [0, 1.0, 0.5],
    'steelblue': [0.277, 0.512, 0.707],
    'tan': [0.824, 0.707, 0.551],
    'teal': [0, 0.504, 0.504],
    'thistle': [0.848, 0.75, 0.848],
    'tomato': [1.0, 0.391, 0.281],
    'turquoise': [0.254, 0.879, 0.816],
    'violet': [0.934, 0.512, 0.934],
    'wheat': [0.961, 0.871, 0.703],
    'white': [1.0, 1.0, 1.0],
    'whitesmoke': [0.961, 0.961, 0.961],
    'yellow': [1.0, 1.0, 0],
    'yellowgreen': [0.605, 0.805, 0.199]
}

ColorType = Union[int, float, str, list, tuple]
class PDFColor:
    """Class that generates a PDF color string (with function ``str()``)
    using the rules described in :func:`pdfme.color.parse_color`.

    Args:
        color (int, float, list, tuple, str, PDFColor): The color
            specification.
        stroke (bool, optional): Whether this is a color for stroke(True)
            or for fill(False). Defaults to False.
    """

    def __init__(
        self, color: Union[ColorType, 'PDFColor'], stroke: bool=False
    ) -> None:
        if isinstance(color, PDFColor):
            self.color = copy(color.color)
        else:
            self.color = parse_color(color)
        self.stroke = stroke

    def __eq__(self, color):
        if color is None: return self.color is None
        if not isinstance(color, PDFColor):
            return False
        return self.color == color.color and self.stroke == color.stroke

    def __neq__(self, color):
        if color is None: return not self.color is None
        if not isinstance(color, PDFColor):
            raise TypeError("Can't compare PDFColor with {}".format(type(color)))
        return self.color != color.color or self.stroke != color.stroke

    def __str__(self):
        if self.color is None:
            return ''
        if len(self.color) == 1:
            return '{} {}'.format(
                round(self.color[0], 3), 'G' if self.stroke else 'g'
            )
        if len(self.color) == 3:
            return '{} {} {} {}'.format(
                *[round(color, 3) for color in self.color[0:3]],
                'RG' if self.stroke else 'rg'
            )

def parse_color(color: ColorType) -> list:
    """Function to parse ``color`` into a list representing a PDF color.

    The scale of the colors is between 0 and 1, instead of 0 and 256, so all the
    numbers in ``color`` must be between 0 and 1.

    ``color`` of type int or float represents a gray color between black (0) and
    white (1).

    ``color`` of type list or tuple is a gray color if its length is 1, a rgb
    color if its length is 3, and a rgba color if its length is 4 (not yet
    supported).

    ``color`` of type str can be a hex color of the form "#aabbcc", the name
    of a color in the variable ``colors`` in file `color.py`_, or a space
    separated list of numbers, that is parsed as an rgb color, like
    the one described before in the list ``color`` type.

    Args:
        color (int, float, list, tuple, str): The color specification.

    Returns:
        list: list representing the PDF color.

    .. _color.py: https://github.com/aFelipeSP/pdfme/blob/main/pdfme/color.py
    """

    if color is None:
        return None
    if isinstance(color, (int, float)):
        return [color]
    if isinstance(color, str):
        if color is '':
            return None
        elif color in colors:
            return colors[color]
        elif color[0] == '#' and len(color) in [4,5,7,9]:
            try: int(color[1:], 16)
            except:
                raise TypeError("Couldn't parse hexagesimal color value: {}".format(color))

            n = len(color)
            if n in [4, 5]:
                return [int(color[i:1+i] + color[i:1+i], 16)/255 for i in range(1,4)]
            else:
                return [int(color[i:2+i], 16)/255 for i in range(1,7,2)]
        else:
            color = re.split(',| ', color)

    if not isinstance(color, (list, tuple)):
        raise TypeError('Invalid color value type: {}'.format(type(color)))

    if len(color) == 1:
        v = color[0]
        if isinstance(v, str):
            try:
                return [float(v)]
            except:
                raise TypeError("Couldn't parse numeric color value: {}".format(v))
        elif isinstance(v, (int, float)):
            return [v]
        else:
            raise TypeError("Invalid color value type: {}".format(type(v)))
    elif len(color) in [3,4]:
        try:
            return [float(c) for c in color[:4]]
        except:
            raise TypeError("Couldn't parse numeric color value: {}".format(color))

from .utils import copy
