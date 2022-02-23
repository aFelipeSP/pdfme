from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing.sharedctypes import Value
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from pdfme.color import ColorType, PDFColor, parse_color
from pdfme.types import Number
from pdfme.utils import format_round

CIRCLE_BEZIER_K = 0.5519150244935105707435627


class PDFGraphicStyle(ABC):
    pass


class LineWidth(PDFGraphicStyle):
    def __init__(self, width: Number):
        self.width = width

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LineWidth):
            return False
        return self.width == other.width

    def __neq__(self, other: Any) -> bool:
        return not self == other

    def __str__(self):
        return '{} w'.format(round(self.width, 3))


class LineCapEnum(Enum):
    BUTT = 0
    ROUND = 1
    SQUARE = 2


class LineCap(PDFGraphicStyle):
    def __init__(self, style: LineCapEnum):
        self.style = style

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LineCap):
            return False
        return self.style == other.style

    def __neq__(self, other: Any) -> bool:
        return not self == other

    def __str__(self):
        return '{} J'.format(self.style.value)


class LineJoinEnum(Enum):
    MILTER = 0
    ROUND = 1
    BEVEL = 2


class LineJoin(PDFGraphicStyle):
    def __init__(self, style: LineJoinEnum):
        self.style = style

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LineJoin):
            return False
        return self.style == other.style

    def __neq__(self, other: Any) -> bool:
        return not self == other

    def __str__(self):
        return '{} j'.format(self.style.value)


class DashPattern(PDFGraphicStyle):
    def __init__(self, on_units: Number, off_units: Number, phase: Number):
        if on_units < 0 or off_units < 0 or phase < 0:
            raise ValueError('Negative numbers not allowed.')
        
        self.on_units, self.off_units, self.phase = on_units, off_units, phase


    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DashPattern):
            return False
        return (
            self.on_units == other.on_units and
            self.off_units == other.off_units and
            self.off_units == other.off_units
        )

    def __neq__(self, other: Any) -> bool:
        return not self == other

    def __str__(self):
        phase = round(self.phase, 3)
        on_units = round(self.on_units, 3)
        off_units = round(self.off_units, 3)
        if self.on_units == self.off_units:
            if self.on_units == 0:
                return '[] {} d'.format(phase)
            else:
                return '[{}] {} d'.format(on_units, phase)
        return '[{} {}] {} d'.format(on_units, off_units, phase)


class Color(PDFGraphicStyle):
    def __init__(self, color: Optional[ColorType]):
        self.color = parse_color(color)

    def __eq__(self, other) -> bool:
        if other is None: return self.color is None
        if not isinstance(other, Color):
            return False
        return self.color == other.color

    def __neq__(self, other) -> bool:
        return not self == other


class FillColor(Color):
    def __str__(self):
        if self.color is None:
            return ''
        if len(self.color) == 1:
            return '{} g'.format(round(self.color[0], 3))
        if len(self.color) == 3:
            return format_round('{} {} {} rg', self.color[0:3])


class StrokeColor(Color):
    def __str__(self):
        if self.color is None:
            return ''
        if len(self.color) == 1:
            return '{} G'.format(round(self.color[0], 3))
        if len(self.color) == 3:
            return format_round('{} {} {} RG', self.color[0:3])


class LineStyleEnum(Enum):
    SOLID = 0
    DASHED = 1
    DOTTED = 2


def build_line_style(
    style: LineStyleEnum, width: Number
) -> Tuple[LineCap, DashPattern]:
    w = width
    if style == LineStyleEnum.DASHED:
        return (LineCap(LineCapEnum.BUTT), DashPattern(w * 3, w * 1.5, 0))
    elif style == LineStyleEnum.DOTTED:
        return (LineCap(LineCapEnum.ROUND), DashPattern(0, w * 2, w * 0.5))
    elif style == LineStyleEnum.SOLID:
        return (LineCap(LineCapEnum.BUTT), DashPattern(0, 0, 0))
    else:
        raise TypeError("style must be a LineStyleEnum option.")


class PDFGraphic(ABC):
    def __init__(
        self,
        fill: Optional[FillColor] = None,
        stroke: Optional[StrokeColor] = None,
        line_width: Number = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
    ):
        self.fill = FillColor(None) if fill is None else fill
        self.stroke = FillColor(0) if stroke is None else stroke
        self.line_width = LineWidth(line_width)
        self.line_cap, self.dash_pattern = build_line_style(
            line_style, line_width
        )
        self.line_join = LineJoin(line_join)

    def style_list(self) -> List[PDFGraphicStyle]:
        return [
            self.line_width,
            self.line_cap,
            self.dash_pattern,
            self.line_join,
            self.fill,
            self.stroke,
        ]

    @abstractmethod
    def definition(self) -> str:
        pass


class Line(PDFGraphic):
    def __init__(
        self,
        x1: Number,
        y1: Number,
        x2: Number,
        y2: Number,
        stroke: Optional[StrokeColor] = None,
        line_width: Number = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER
    ):
        super().__init__(None, stroke, line_width, line_style, line_join)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def definition(self) -> str:
        coords = self.x1, self.y1, self.x2, self.y2
        return format_round('{} {} m {} {} l S', coords)


class PDFBoxSizing(Enum):
    CONTENT = 0
    BORDER = 1


class Rectangle(PDFGraphic):
    def __init__(
        self,
        x: Number,
        y: Number,
        width: Number,
        height: Number,
        fill: Optional[FillColor] = None,
        stroke: Optional[StrokeColor] = None,
        line_width: Number = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
        box_sizing: PDFBoxSizing = PDFBoxSizing.BORDER,
        border_radius: Number = 0
    ):
        super().__init__(fill, stroke, line_width, line_style, line_join)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.box_sizing = box_sizing
        self.border_radius = border_radius

    def definition(self) -> str:
        w, h = self.width, self.height
        if self.box_sizing == PDFBoxSizing.BORDER:
            w -= self.line_width.width
            h -= self.line_width.width
        elif self.box_sizing == PDFBoxSizing.CONTENT:
            w += self.line_width.width
            h += self.line_width.width

        x, y = self.x, self.y

        if self.border_radius == 0:
            path = format_round('{} {} {} {} re', (x, y, w, h))
        else:
            r = min(min(w/2, h/2), self.border_radius)
            c = CIRCLE_BEZIER_K * r
            w -= r * 2
            h -= r * 2
            y += r
            path = format_round('{} {} m', (x, y))
            y += h
            path += format_round(' {} {} l {} {}', (x, y, x, y + c))
            y += r
            x += r
            path += format_round(' {} {} {} {} c', (x - c, y, x, y))
            x += w
            path += format_round(' {} {} l {} {}', (x, y, x + c, y))
            y -= r
            x += r
            path += format_round(' {} {} {} {} c', (x, y + c, x, y))
            y -= h
            path += format_round(' {} {} l {} {}', (x, y, x, y - c))
            y -= r
            x -= r
            path += format_round(' {} {} {} {} c', (x + c, y, x, y))
            x -= w
            path += format_round(' {} {} l {} {}', (x, y, x - c, y))
            y += r
            x -= r
            path += format_round(' {} {} {} {} c', (x, y - c, x, y))

        if self.stroke.color is not None and self.fill.color is not None:
            path += ' b'
        elif self.stroke.color is not None:
            path += ' s'
        elif self.fill.color is not None:
            path += ' h f'

        return path


class Ellipse(PDFGraphic):
    def __init__(
        self,
        cx: Number,
        cy: Number,
        rx: Number,
        ry: Number,
        fill: Optional[FillColor] = None,
        stroke: Optional[StrokeColor] = None,
        line_width: Number = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
        box_sizing: PDFBoxSizing = PDFBoxSizing.BORDER
    ):
        super().__init__(fill, stroke, line_width, line_style, line_join)
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.box_sizing = box_sizing

    def definition(self) -> str:
        rx, ry = self.rx, self.ry
        if self.box_sizing == PDFBoxSizing.BORDER:
            rx -= self.line_width.width / 2
            ry -= self.line_width.width / 2
        elif self.box_sizing == PDFBoxSizing.CONTENT:
            rx += self.line_width.width / 2
            ry += self.line_width.width / 2

        cx, cy = self.cx, self.cy

        kx = CIRCLE_BEZIER_K * rx
        ky = CIRCLE_BEZIER_K * ry
        x = cx - rx
        y = cy
        path = format_round('{} {} m {} {}', (x, y, x, y+ky))
        y += ry
        x += rx
        path += format_round(' {} {} {} {} c {} {}', (x-kx, y, x, y, x+kx, y))
        y -= ry
        x += rx
        path += format_round(' {} {} {} {} c {} {}', (x, y+ky, x, y, x, y-ky))
        y -= ry
        x -= rx
        path += format_round(' {} {} {} {} c {} {}', (x+kx, y, x, y, x-kx, y))
        y += ry
        x -= rx
        path += format_round(' {} {} {} {} c', (x, y-ky, x, y))

        if self.stroke.color is not None and self.fill.color is not None:
            path += ' b'
        elif self.stroke.color is not None:
            path += ' s'
        elif self.fill.color is not None:
            path += ' h f'

        return path

class PathPart:
    pass

class PathMove(PathPart):
    def __init__(self, x: Number, y: Number):
        self.x = x
        self.y = y

    def __str__(self):
        return format_round('{} {} m', (self.x, self.y))

class PathLine(PathPart):
    def __init__(self, x: Number, y: Number):
        self.x = x
        self.y = y

    def __str__(self):
        return format_round('{} {} l', (self.x, self.y))

class PathCurve(PathPart):
    def __init__(
        self,
        x1: Number,
        y1: Number,
        x2: Number,
        y2: Number,
        x3: Number,
        y3: Number
    ):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3

    def __str__(self):
        coords = (self.x1, self.y1, self.x2, self.y2, self.x3, self.y3)
        return format_round('{} {} {} {} {} {} c', coords)

class PathEnd(PathPart):
    def __str__(self):
        return 'h'

class Path(PDFGraphic):
    def __init__(
        self,
        path_parts: List[PathPart],
        fill: Optional[FillColor] = None,
        stroke: Optional[StrokeColor] = None,
        line_width: Number = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER
    ):
        super().__init__(fill, stroke, line_width, line_style, line_join)
        self.path_parts = path_parts

    def definition(self) -> str:
        path = ' '.join(str(path_part) for path_part in self.path_parts)
        if self.stroke.color is not None and self.fill.color is not None:
            path += ' B'
        elif self.stroke.color is not None:
            path += ' S'
        elif self.fill.color is not None:
            path += ' f'

        return path


def create_graphics(graphics: List[PDFGraphic]) -> str:
    """Function to transform a list of graphics dicts (with lines and fill
    rectangles) into a PDF stream, ready to be added to a PDF page stream.

    Args:
        graphics (list): list of graphics dicts.

    Returns:
        str: a PDF stream containing the passed graphics.
    """

    styles: Dict[Any, PDFGraphicStyle] = {}
    stream = []

    for graphic in graphics:
        for style in graphic.style_list():
            style_class = style.__class__
            if style_class not in styles or (styles[style_class] != style):
                stream.append(str(style))
                styles[style_class] = style

        stream.append(graphic.definition())

    if len(stream):
        return 'q' + (' '.join(stream))+ ' Q'
    else:
        return ''