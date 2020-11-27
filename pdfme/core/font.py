from .base import PDFObject
from ..utils import subs

STANDARD_FONTS = ['Times-Roman', 'Helvetica', 'Courier', 'Symbol',
    'Times-Bold', 'Helvetica-Bold', 'Courier-Bold', 'ZapfDingbats', 
    'Times-Italic', 'Helvetica-Oblique', 'Courier-Oblique', 
    'Times-BoldItalic', 'Helvetica-BoldOblique', 'Courier-BoldOblique']

class PDFFont(PDFObject):
    def __init__(self, id_, subtype):
        super().__init__(id_)
        self.subtype = subtype

class PDFFontStandard(PDFFont):
    def __init__(self, id_, name):
        super().__init__(id_)
        if not name in STANDARD_FONTS:
            raise Exception('name must be one of the 14 standar '
                'fonts: ' + str(STANDARD_FONTS))
        self.name = name

    def output(self):
        return {
            'Type': b'/Font',
            'Subtype': b'/Type1',
            'BaseFont': subs('/{}', self.name)
        }


# class PDFFontType1(PDFFont):
#     def __init__(self, id_, BaseFont, FirstChar, LastChar, Widths,FontDescriptor):
#         super().__init__(id_, 'Type1')
#         assert isinstance(BaseFont, str)
#         self.BaseFont = subs('/{}', BaseFont)
#         assert isinstance(FirstChar, int)
#         self.FirstChar = FirstChar
#         assert isinstance(LastChar, int)
#         self.LastChar = LastChar
#         assert isinstance(Widths, (list, tuple))
#         self.Widths = Widths
#         self.FontDescriptor = FontDescriptor

#     def output(self):
#         ret = {
#             'ExtGState': {k: v.ref for k, v in self.ExtGState.items()},
#             'XObject': {k: v.ref for k, v in self.XObject.items()},
#             'Font': {k: v.ref for k, v in self.Font.items()}
#         }

#         return ret