from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple


CIRCLE_BEZIER_K = 0.5519150244935105707435627


class PDFGraphicStyle(ABC):
    pass


class LineWidth(PDFGraphicStyle):
    def __init__(self, width: "Number"):
        self.width = width

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LineWidth):
            return False
        return self.width == other.width

    def __neq__(self, other: Any) -> bool:
        return not self == other

    def __str__(self):
        return "{} w".format(round(self.width, 3))


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
        return "{} J".format(self.style.value)


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
        return "{} j".format(self.style.value)


class DashPattern(PDFGraphicStyle):
    def __init__(self, on_units: "Number", off_units: "Number", phase: "Number"):
        if on_units < 0 or off_units < 0 or phase < 0:
            raise ValueError("Negative numbers not allowed.")

        self.on_units, self.off_units, self.phase = on_units, off_units, phase

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DashPattern):
            return False
        return (
            self.on_units == other.on_units
            and self.off_units == other.off_units
            and self.off_units == other.off_units
        )

    def __neq__(self, other: Any) -> bool:
        return not self == other

    def __str__(self):
        phase = round(self.phase, 3)
        on_units = round(self.on_units, 3)
        off_units = round(self.off_units, 3)
        if self.on_units == self.off_units:
            if self.on_units == 0:
                return "[] {} d".format(phase)
            else:
                return "[{}] {} d".format(on_units, phase)
        return "[{} {}] {} d".format(on_units, off_units, phase)


class Color(PDFGraphicStyle):
    def __init__(self, color: Optional["ColorType"]):
        self.color = parse_color(color)

    def __eq__(self, other) -> bool:
        if other is None:
            return self.color is None
        if not isinstance(other, Color):
            return False
        return self.color == other.color

    def __neq__(self, other) -> bool:
        return not self == other


class FillColor(Color):
    def __str__(self):
        if self.color is None:
            return ""
        if len(self.color) == 1:
            return "{} g".format(round(self.color[0], 3))
        if len(self.color) == 3:
            return format_round("{} {} {} rg", self.color[0:3])


class StrokeColor(Color):
    def __str__(self):
        if self.color is None:
            return ""
        if len(self.color) == 1:
            return "{} G".format(round(self.color[0], 3))
        if len(self.color) == 3:
            return format_round("{} {} {} RG", self.color[0:3])


class LineStyleEnum(Enum):
    SOLID = 0
    DASHED = 1
    DOTTED = 2


def build_line_style(
    style: LineStyleEnum, width: "Number"
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


class BoundingRect:
    def __init__(self):
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None

    def update(self, x: "Number", y: "Number"):
        self.x1 = x if self.x1 is None else min(self.x1, x)
        self.y1 = y if self.y1 is None else min(self.y1, y)
        self.x2 = x if self.x2 is None else max(self.x2, x)
        self.y2 = y if self.y2 is None else max(self.y2, y)

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1

    @property
    def all(self):
        return [self.x1, self.y1, self.x2, self.y2, self.width, self.height]


class PDFGraphicBase(ABC):
    def style_list(self) -> List[PDFGraphicStyle]:
        return []

    @abstractmethod
    def definition(self) -> str:
        pass

    @abstractmethod
    def bounding_rect(self) -> BoundingRect:
        pass


class PDFGraphic(PDFGraphicBase):
    def __init__(
        self,
        stroke: "ColorType" = 0,
        fill: Optional["ColorType"] = None,
        line_width: "Number" = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
        line_cap: Optional[LineCapEnum] = None,
        dash_pattern: Optional[DashPattern] = None,
    ):
        self.fill = FillColor(fill)
        self.stroke = StrokeColor(stroke)
        self.line_width = LineWidth(line_width)
        self.line_cap, self.dash_pattern = build_line_style(line_style, line_width)
        if line_cap is not None:
            self.line_cap = LineCap(line_cap)
        if dash_pattern is not None:
            self.dash_pattern = dash_pattern

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


def path_move(x, y):
    return format_round("{} {} m", (x, y))


def path_line(x, y):
    return format_round("{} {} l", (x, y))


def path_curve(x1, y1, x2, y2, x3, y3):
    return format_round("{} {} {} {} {} {} c", (x1, y1, x2, y2, x3, y3))


def path_close():
    return "h"


class Path(PDFGraphic):
    def __init__(
        self,
        path: str,
        stroke: "ColorType" = 0,
        fill: Optional["ColorType"] = None,
        line_width: "Number" = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
        line_cap: Optional[LineCapEnum] = None,
        dash_pattern: Optional[DashPattern] = None,
    ):
        super().__init__(
            stroke, fill, line_width, line_style, line_join, line_cap, dash_pattern
        )
        self.path = path

    def definition(self) -> str:
        path = self.path
        if self.stroke.color is not None and self.fill.color is not None:
            path += " B"
        elif self.stroke.color is not None:
            path += " S"
        elif self.fill.color is not None:
            path += " f"

        return path

    def bounding_rect(self) -> BoundingRect:
        rect = BoundingRect()
        parts = self.path.split(" ")
        args = []
        for part in parts:
            part = part.strip()
            if part.isnumeric():
                args.append(float(part))
                continue
            elif part == "m" and len(args) == 2:
                rect.update(*args)
            elif part == "l" and len(args) == 2:
                rect.update(*args)
            elif part == "c" and len(args) == 6:
                rect.update(*args[4:])
            elif part == "v" and len(args) == 4:
                rect.update(*args[2:])
            elif part == "y" and len(args) == 4:
                rect.update(*args[2:])
            elif part == "h":
                pass
            else:
                raise ValueError("incorrect format path:" + self.path)
            args = []

        return rect


class Line(PDFGraphic):
    def __init__(
        self,
        x1: "Number",
        y1: "Number",
        x2: "Number",
        y2: "Number",
        stroke: "ColorType" = 0,
        line_width: "Number" = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
        line_cap: Optional[LineCapEnum] = None,
        dash_pattern: Optional[DashPattern] = None,
    ):
        super().__init__(
            stroke, None, line_width, line_style, line_join, line_cap, dash_pattern
        )
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def definition(self) -> str:
        coords = self.x1, self.y1, self.x2, self.y2
        return format_round("{} {} m {} {} l S", coords)

    def bounding_rect(self) -> BoundingRect:
        rect = BoundingRect()
        rect.update(self.x1, self.y1)
        rect.update(self.x2, self.y2)
        return rect


class PDFBoxSizing(Enum):
    BORDER = 0
    NORMAL = 1
    CONTENT = 2


class Rectangle(PDFGraphic):
    def __init__(
        self,
        x: "Number",
        y: "Number",
        width: "Number",
        height: "Number",
        stroke: "ColorType" = 0,
        fill: Optional["ColorType"] = None,
        line_width: "Number" = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
        line_cap: Optional[LineCapEnum] = None,
        dash_pattern: Optional[DashPattern] = None,
        box_sizing: PDFBoxSizing = PDFBoxSizing.BORDER,
        border_radius: "Number" = 0,
    ):
        super().__init__(
            stroke, fill, line_width, line_style, line_join, line_cap, dash_pattern
        )
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.box_sizing = box_sizing
        self.border_radius = border_radius

    def _get_real_coords(self):
        x, y, w, h = self.x, self.y, self.width, self.height
        line_width = 0 if self.stroke.color is None else self.line_width.width
        if self.box_sizing == PDFBoxSizing.BORDER:
            w -= line_width
            h -= line_width
            x += line_width / 2
            y += line_width / 2
        elif self.box_sizing == PDFBoxSizing.CONTENT:
            w += line_width
            h += line_width
            x -= line_width / 2
            y -= line_width / 2

        return x, y, w, h, line_width

    def definition(self) -> str:
        x, y, w, h, line_width = self._get_real_coords()

        if self.border_radius == 0:
            path = format_round("{} {} {} {} re", (x, y, w, h))
        else:
            r = min(min(w / 2, h / 2), self.border_radius)
            c = CIRCLE_BEZIER_K * r
            w -= r * 2
            h -= r * 2
            y += r
            path = " " + path_move(x, y)
            y += h
            path += " " + path_line(x, y)
            x += r
            y += r
            path += " " + path_curve(x - r, y - r + c, x - c, y, x, y)
            x += w
            path += " " + path_line(x, y)
            x += r
            y -= r
            path += " " + path_curve(x - r + c, y + r, x, y + c, x, y)
            y -= h
            path += " " + path_line(x, y)
            x -= r
            y -= r
            path += " " + path_curve(x + r, y + r - c, x + c, y, x, y)
            x -= w
            path += " " + path_line(x, y)
            x -= r
            y += r
            path += " " + path_curve(x + r - c, y - r, x, y - c, x, y)

        if line_width > 0 and self.fill.color is not None:
            path += " b"
        elif line_width > 0:
            path += " s"
        elif self.fill.color is not None:
            path += " h f"

        return path

    def bounding_rect(self) -> BoundingRect:
        rect = BoundingRect()
        x, y, w, h, line_width = self._get_real_coords()
        line_width_half = line_width / 2
        x1 = x - line_width_half
        y1 = y - line_width_half
        x2 = x + w + line_width_half
        y2 = y + h + line_width_half
        rect.update(x1, y1)
        rect.update(x2, y2)
        return rect


class Ellipse(PDFGraphic):
    def __init__(
        self,
        cx: "Number",
        cy: "Number",
        rx: "Number",
        ry: "Number",
        stroke: "ColorType" = 0,
        fill: Optional["ColorType"] = None,
        line_width: "Number" = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
        line_cap: Optional[LineCapEnum] = None,
        dash_pattern: Optional[DashPattern] = None,
        box_sizing: PDFBoxSizing = PDFBoxSizing.BORDER,
    ):
        super().__init__(
            stroke, fill, line_width, line_style, line_join, line_cap, dash_pattern
        )
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.box_sizing = box_sizing

    def _get_real_coords(self):
        rx, ry = self.rx, self.ry
        line_width = 0 if self.stroke.color is None else self.line_width.width
        if self.box_sizing == PDFBoxSizing.BORDER:
            rx -= line_width / 2
            ry -= line_width / 2
        elif self.box_sizing == PDFBoxSizing.CONTENT:
            rx += line_width / 2
            ry += line_width / 2

        return rx, ry, line_width

    def definition(self) -> str:
        rx, ry, line_width = self._get_real_coords()
        cx, cy = self.cx, self.cy

        kx = CIRCLE_BEZIER_K * rx
        ky = CIRCLE_BEZIER_K * ry
        path = " ".join(
            [
                path_move(cx - rx, cy),
                path_curve(cx - rx, cy + ky, cx - kx, cy + ry, cx, cy + ry),
                path_curve(cx + kx, cy + ry, cx + rx, cy + ky, cx + rx, cy),
                path_curve(cx + rx, cy - ky, cx + kx, cy - ry, cx, cy - ry),
                path_curve(cx - kx, cy - ry, cx - rx, cy - ky, cx - rx, cy),
            ]
        )
        if line_width > 0 and self.fill.color is not None:
            path += " b"
        elif line_width > 0:
            path += " s"
        elif self.fill.color is not None:
            path += " h f"

        return path

    def bounding_rect(self) -> BoundingRect:
        rect = BoundingRect()
        rx, ry, line_width = self._get_real_coords()
        line_width_half = line_width / 2
        x1 = self.cx - rx - line_width_half
        y1 = self.cy - ry - line_width_half
        x2 = self.cx + rx + line_width_half
        y2 = self.cy + ry + line_width_half
        rect.update(x1, y1)
        rect.update(x2, y2)
        return rect


class Text(PDFGraphic):
    def __init__(
        self,
        content: "ContentType",
        x: "Number",
        y: "Number",
        width: "Number",
        pdf: "PDF",
        padding: "MarginType" = 0,
        stroke: "ColorType" = 0,
        fill: Optional["ColorType"] = None,
        line_width: "Number" = 1,
        line_style: LineStyleEnum = LineStyleEnum.SOLID,
        line_join: LineJoinEnum = LineJoinEnum.MILTER,
        line_cap: Optional[LineCapEnum] = None,
        dash_pattern: Optional[DashPattern] = None,
        box_sizing: PDFBoxSizing = PDFBoxSizing.BORDER,
        border_radius: "Number" = 0,
        paragraph_style: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            stroke, fill, line_width, line_style, line_join, line_cap, dash_pattern
        )
        self.content = content
        self.x = x
        self.y = y
        self.width = width
        self.paragraph_style = paragraph_style or {}
        self.pdf = pdf
        self.padding = parse_margin(padding)
        self._rect = Rectangle(
            x,
            y,
            width,
            0,
            stroke,
            fill,
            line_width,
            line_style,
            line_join,
            line_cap,
            dash_pattern,
            box_sizing,
            border_radius,
        )

    def definition(self):
        x, y, w, _, line_width = self._rect._get_real_coords()
        w -= line_width + self.padding["right"] + self.padding["left"]
        x += line_width / 2 + self.padding["left"]
        y += line_width / 2 + self.padding["bottom"]

        paragraph_style = {
            v: self.paragraph_style.get(v)
            for v in PARAGRAPH_PROPERTIES
            if v in self.paragraph_style
        }

        self.pdf_text = PDFText(
            self.content, w, 1e6, fonts=self.pdf.fonts, pdf=self.pdf, **paragraph_style
        )
        self.pdf_text.run()
        for font in self.pdf_text.used_fonts:
            self.pdf._used_font(*font)

        real_y = y + self.pdf_text.current_height

        self._rect.height = (
            self.pdf_text.current_height
            + line_width * 2
            + self.padding["top"]
            + self.padding["bottom"]
        )
        stream = self._rect.definition()
        stream += " BT 1 0 0 1 {} {} Tm{} ET".format(x, real_y, self.pdf_text.text)
        return stream

    def bounding_rect(self) -> BoundingRect:
        return self._rect.bounding_rect()


class PDFGraphics:
    def __init__(
        self,
        graphics: Iterable[PDFGraphic],
        x: "Number"=0,
        y: "Number"=0,
        width: Optional["Number"]=None,
        height: Optional["Number"]=None
    ):
        self.graphics = graphics
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.result: Optional[str] = None
        self.rect = BoundingRect()
        self.run()

    def run(self) -> str:
        """Function to transform a list of graphics objects into a PDF stream,
        ready to be added to a PDF page stream.

        Args:
            graphics (List[PDFGraphic]): list of graphics dicts.

        Returns:
            str: a PDF stream containing the passed graphics.
        """

        styles: Dict[Any, PDFGraphicStyle] = {}
        stream = []
        self.rect = BoundingRect()
        for graphic in self.graphics:
            for style in graphic.style_list():
                style_class = style.__class__
                if style_class not in styles or (styles[style_class] != style):
                    style_str = str(style)
                    if style_str != "":
                        stream.append(str(style))
                        styles[style_class] = style

            stream.append(graphic.definition())
            element_rect = graphic.bounding_rect()
            self.rect.update(*element_rect.all[:2])
            self.rect.update(*element_rect.all[2:4])

        self.result = " ".join(stream)

        h = self.rect.height
        w = self.rect.width

        if self.width is None and self.height is None:
            self.width = w
            self.height = h
        elif self.width is None:
            self.width = self.height * w / h
        elif self.height is None:
            self.height = self.width * h / w

        self.result = "q {} 0 0 {} {} {} cm {} Q".format(
            round(self.width / w, 3), round(self.height / h, 3),
            round(self.x, 3), round(self.y, 3),
            " ".join(stream)
        )
        
        return self.result


GRAPHIC_STYLE_MAP = {
    "line_style": LineStyleEnum,
    "line_join": LineJoinEnum,
    "box_sizing": PDFBoxSizing,
    "line_cap": LineCapEnum,
}


def create_graphics_from_dicts(
    items: Iterable[Dict[str, Any]], 
    pdf: "PDF",
    x: "Number"=0,
    y: "Number"=0,
    width: Optional["Number"]=None,
    height: Optional["Number"]=None,
) -> PDFGraphics:
    """Function to transform a list of graphics dicts into a PDF stream, ready
    to be added to a PDF page stream.

    Args:
        items (Iterable[Dict[str, Any]]): list of graphics dicts.

    Returns:
        str: a PDF stream containing the passed graphics.
    """
    graphics: List[Any] = []
    for graphic_dict_original in items:
        graphic_dict = graphic_dict_original.copy()

        for graphic_style_name, graphic_style in GRAPHIC_STYLE_MAP.items():
            if graphic_style_name in graphic_dict:
                option = graphic_dict[graphic_style_name].upper()
                graphic_dict[graphic_style_name] = graphic_style[option]

        if "dash_pattern" in graphic_dict:
            option = graphic_dict["dash_pattern"]
            graphic_dict["dash_pattern"] = DashPattern(**option)

        type_ = graphic_dict.pop("type")
        if type_ == "line":
            graphics.append(Line(**graphic_dict))
        elif type_ == "ellipse":
            graphics.append(Ellipse(**graphic_dict))
        elif type_ == "rect":
            graphics.append(Rectangle(**graphic_dict))
        elif type_ == "path":
            graphics.append(Path(**graphic_dict))
        elif type_ == "text":
            graphics.append(Text(pdf=pdf, **graphic_dict))

    return PDFGraphics(graphics, x, y, width, height)


from pdfme.color import ColorType, parse_color
from pdfme.pdf import PDF
from pdfme.text import PDFText, ContentType
from pdfme.types import MarginType, Number
from pdfme.utils import format_round, PARAGRAPH_PROPERTIES, parse_margin
