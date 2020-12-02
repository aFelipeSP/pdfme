import copy
import struct
from pathlib import Path

from .utils import get_page_size, subs
from . import standard_fonts as std_font
from .base import PDFBase
from .text import PDFText

STANDARD_FONTS = {
    'Helvetica': {
        'n': { 'ref': 'F1', 'base_font': 'Helvetica', 'widths': std_font.helvetica },
        'b': { 'ref': 'F1b', 'base_font': 'Helvetica-Bold', 'widths': std_font.helveticaB },
        'i': { 'ref': 'F1i', 'base_font': 'Helvetica-Oblique', 'widths': std_font.helvetica},
        'bi': { 'ref': 'F1bi', 'base_font': 'Helvetica-BoldOblique', 'widths': std_font.helveticaB }
    },
    'Times': {
        'n': { 'ref': 'F2', 'base_font': 'Times-Roman', 'widths': std_font.times },
        'b': { 'ref': 'F2b', 'base_font': 'Times-Bold', 'widths': std_font.timesB },
        'i': { 'ref': 'F2i', 'base_font': 'Times-Italic', 'widths': std_font.timesI },
        'bi': { 'ref': 'F2bi', 'base_font': 'Times-BoldItalic', 'widths': std_font.timesBI }
    },
    'Courier': {
        'n': { 'ref': 'F3', 'base_font': 'Courier', 'widths': std_font.courier },
        'b': { 'ref': 'F3b', 'base_font': 'Courier-Bold', 'widths': std_font.courier },
        'i': { 'ref': 'F3i', 'base_font': 'Courier-Oblique', 'widths': std_font.courier },
        'bi': { 'ref': 'F3bi', 'base_font': 'Courier-BoldOblique', 'widths': std_font.courier }
    },
    'Symbol': { 'n': { 'ref': 'F4', 'base_font': 'Symbol', 'widths': std_font.symbol } },
    'ZapfDingbats': { 'n': { 'ref': 'F5', 'base_font': 'ZapfDingbats', 'widths': std_font.zapfdingbats } }
}
class PDF:
    def __init__(self, page_size='a4', portrait=True, margins=56.6929,
        font_family='Helvetica',
        font_size=11,
        stroke_width=1,
        fill_color='black',
        stroke_color='white',
        text_align='l',
        line_height=1.1,
    ):

        self.page_width, self.page_height = get_page_size('a4')
        self.portrait = portrait

        if isinstance(margins, (int, float)):
            margins = [margins]

        if len(margins) == 1:
            self.margins = margins * 4
        elif len(margins) == 2:
            self.margins = margins * 2
        elif len(margins) == 3:
            self.margins = margins.append(margins[1])

        self.width = self.page_width - self.margins[1] - self.margins[3]
        self.height = self.page_height - self.margins[0] - self.margins[2]

        self.font_family = font_family
        self.font_size = font_size
        self.stroke_width = stroke_width
        self.fill_color = fill_color
        self.stroke_color = stroke_color
        self.text_align = text_align
        self.line_height = line_height

        self.pages = []
        self.page_count = 0

        self.base = PDFBase()
        self.root = self.base.add({ 'Type': b'/Catalog'})
        self.base.trailer['Root'] = self.root.id

        self.fonts_data = copy.deepcopy(STANDARD_FONTS)
        self.font_count = 6
        self.used_fonts = {}
        self._add_font('Helvetica', 'n')
        
        self.add_page()

        self.images = {}

    @property
    def y(self):
        return self.page_height - self._y

    @y.setter
    def y(self, value):
        self._y = self.page_height - value

    def move_x(self, x):
        self.x += x

    def move_y(self, y):
        self.y += y

    def move(self, x, y):
        self.move_x(x)
        self.move_y(y)

    def add_font(self, font_family, font_files):
        raise NotImplementedError()

    def add_page(self, page_size=None, portrait=None):
        page = self.base.add({ 'Type': b'/Page' })

        self.pages.append(page)
        self.n_page = self.page_count
        self.page_count += 1

        self.x = self.margins[3]
        self._y = self.page_height - self.margins[0]

        if ((page_size is None and portrait is None) or (page_size ==
            [self.page_width, self.page_height] and self.portrait == portrait)
        ): return

        page_size = [self.page_width, self.page_height] if page_size is None \
            else get_page_size(page_size)

        if (portrait is None and not self.portrait) or not portrait:
            page_size = [page_size[1], page_size[0]]

        page['MediaBox'] = [0, 0] + page_size

    @property
    def page(self):
        return self.pages[self.n_page]

    def _build_pages_tree(self, page_list):
        new_page_list = []
        count = 0
        for page_parent in page_list:
            if count % 6 == 0:
                new_page_list.append(
                    self.base.add({'Type': b'/Pages', 'Kids': [], 'Count': 0})
                )
                count += 1

            last_parent = new_page_list[-1]
            page_parent['Parent'] = last_parent.id
            last_parent['Kids'].append(page_parent.id)
            last_parent['Count'] += 1

        if count == 1:
            self.root['Pages'] = new_page_list[0].id

            page_size = [self.page_width, self.page_height] \
                if self.portrait else [self.page_height, self.page_width]

            new_page_list[0]['MediaBox'] = [0, 0] + page_size
        else:
            self._build_pages_tree(new_page_list)


    def stream(self, instructions):
        graphic = self.base.add({'__stream__': instructions })
        if not 'Contents' in self.page: self.page['Contents'] = []
        self.page['Contents'].append(graphic.id)
        

    def image(self, image_path, x, y, width, height):
        if image_path in self.images:
            image_obj = self.images[image_path]
        else:
            with Path(image_path).open('rb') as f:
                try:
                    while True:
                        markerHigh, markerLow = struct.unpack('BB', f.read(2))
                        if markerHigh != 0xFF or markerLow < 0xC0:
                            raise SyntaxError('No JPEG marker found')
                        elif markerLow == 0xDA: # SOS
                            raise SyntaxError('No JPEG SOF marker found')
                        elif (markerLow == 0xC8 or # JPG
                            (markerLow >= 0xD0 and markerLow <= 0xD9) or # RSTx
                            (markerLow >= 0xF0 and markerLow <= 0xFD)): # JPGx
                            continue
                        else:
                            if (
                                (markerLow >= 0xC0 and markerLow <= 0xC3) or # SOF0 - SOF3
                                (markerLow >= 0xC5 and markerLow <= 0xC7) or # SOF4 - SOF7
                                (markerLow >= 0xC9 and markerLow <= 0xCB) or # SOF9 - SOF11
                                (markerLow >= 0xCD and markerLow <= 0xCF) # SOF13 - SOF15
                            ): 
                                data_size, = struct.unpack('>H', f.read(2))
                                data = f.read(data_size - 2) if data_size > 2 else ''

                                depth, h, w, layers = struct.unpack_from('>BHHB', data)

                                if layers == 3: colspace = b'/DeviceRGB'
                                elif layers == 4: colspace = b'/DeviceCMYK'
                                else: colspace = b'/DeviceGray'

                                break
                except Exception:
                    raise ValueError("Couldn't process image in {}".format(image_path))

                f.seek(0)
                image_data = f.read()
                f.close()

            image_obj = self.base.add({
                'Type': b'/XObject',
                'Subtype': b'/Image',
                'Height': int(h),
                'Width': int(w),
                'ColorSpace': colspace,
                'BitsPerComponent': int(depth),
                'Filter': b'/DCTDecode',
                '__stream__': image_data
            })

            self.images[image_path] = image_obj
        
        
        if not 'Resources' in self.page: self.page['Resources'] = {}

        self.page['Resources'].setdefault('XObject', {})
        image_id = 'Im{}'.format(len(self.page['Resources']['XObject']))
        self.page['Resources']['XObject'][image_id] = image_obj.id

        stream = self.base.add({'__stream__':subs('q {} 0 0 {} {} {} cm /{} Do', 
            width, height, x, y, image_id        
        )})

        if not 'Contents' in self.page: self.page['Contents'] = []
        self.page['Contents'].append(stream.id)

    def _add_font(self, font_family, mode):
        font = self.fonts_data[font_family]['n'] \
            if mode not in self.fonts_data[font_family] \
            else self.fonts_data[font_family][mode]

        font_obj = self.base.add({
            'Type': b'/Font',
            'Subtype': b'/Type1',
            'BaseFont': subs('/{}', font['base_font']),
            'Encoding': b'/WinAnsiEncoding'
        })
        self.used_fonts[(font_family, mode)] = font_obj
        return font_obj

    def _used_font(self, font_family, mode):
        font = self.fonts_data[font_family]['n'] \
            if mode not in self.fonts_data[font_family] \
            else self.fonts_data[font_family][mode]

        if (font_family, mode) in self.used_fonts:
            font_obj = self.used_fonts[(font_family, mode)]
        else:
            font_obj = self._add_font(font_family, mode)

        if not 'Resources' in self.page: self.page['Resources'] = {}
        self.page['Resources'].setdefault('Font', {})
        self.page['Resources']['Font'][font['ref']] = font_obj.id

    def text(self, content,
        width = None,
        height = None,
        font_family = None,
        font_size = None,
        text_align = None,
        line_height = None,
        font_weight = 'normal',
        font_style = 'normal',
        color = None,
        move = 'bottom'
    ):

        style = dict(
            width = self.width + self.margins[3] - self.x if width is None else width,
            height = self.height + self.margins[0] - self.y if height is None else height,
            font_family = self.font_family if font_family is None else font_family,
            font_size = self.font_size if font_size is None else font_size,
            text_align = self.text_align if text_align is None else text_align,
            line_height = self.line_height if line_height is None else line_height,
            color = self.fill_color if color is None else color
        )

        pdf_text = PDFText(content, self.fonts_data, **style)
        ret = pdf_text.process()

        for font in pdf_text.used_fonts:
            self._used_font(*font)

        text = self.base.add({'__stream__':
            subs('BT 1 0 0 1 {} {} Tm{} ET', self.x, self._y, pdf_text.stream)})
        if not 'Contents' in self.page: self.page['Contents'] = []
        self.page['Contents'].append(text.id)

        if move == 'bottom':
            self.move_y(pdf_text.current_height)
        if move == 'next':
            self.move_x(pdf_text.width)

        if not ret is None:
            return [ret]


    def output(self, buffer):
        self._build_pages_tree(self.pages)
        self.base.output(buffer)




        
