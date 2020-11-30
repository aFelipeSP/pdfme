import struct
from pathlib import Path

from .utils import get_page_size, subs
from . import standard_fonts as std_font
from .base import PDFBase
class PDF:
    def __init__(self, page_size='a4', portrait=True, font_family='Helvetica',
        font_size=11, line_width=1, fill_color='black', stroke_color='white'
    ):

        self.page_size = get_page_size('a4')
        self.portrait = portrait
        self.font_family = font_family
        self.font_size = font_size
        self.line_width = line_width
        self.fill_color = fill_color
        self.stroke_color = stroke_color

        self.font_widths = {
            'Helvetica': {
                'n': { 'name': 'F1', 'widths': std_font.helvetica },
                'b': { 'name': 'F1b', 'widths': std_font.helveticaB },
                'i': { 'name': 'F1i', 'widths': std_font.helvetica},
                'bi': { 'name': 'F1bi', 'widths': std_font.helveticaB }
            },
            'Times': {
                'n': { 'name': 'F2', 'widths': std_font.times },
                'b': { 'name': 'F2b', 'widths': std_font.timesB },
                'i': { 'name': 'F2i', 'widths': std_font.timesI },
                'bi': { 'name': 'F2bi', 'widths': std_font.timesBI }
            },
            'Courier': {
                'n': { 'name': 'F3', 'widths': std_font.courier },
                'b': { 'name': 'F3b', 'widths': std_font.courier },
                'i': { 'name': 'F3i', 'widths': std_font.courier },
                'bi': { 'name': 'F3bi', 'widths': std_font.courier }
            },
            'Symbol': { 'n': { 'name': 'F4', 'widths': std_font.symbol } },
            'ZapfDingbats': { 'n': { 'name': 'F5', 'widths': std_font.zapfdingbats } }
        }

        self.font_count = 6
        self.fonts_added = set()
        self.page_parents = []
        self.pages = []
        self.page_count = 0

        self.base = PDFBase()
        self.root = self.base.add({ 'Type': b'/Catalog'})
        self.base.trailer['Root'] = self.root.id

        self.add_page()

        self.images = {}

    def add_font(self, font_family, font_files):
        raise NotImplementedError()

    def add_page(self, page_size=None, portrait=None):
        if self.page_count % 6 == 0:
            self.page_parents.append(
                self.base.add({'Type': b'/Pages', 'Kids': [], 'Count': 0})
            )

        last_parent = self.page_parents[-1]
        page = self.base.add({
            'Type': b'/Page',
            'Parent': last_parent.id
        })

        if not page_size is None:
            page_size = get_page_size(page_size)
            if (portrait is None and not self.portrait) or not portrait:
                page_size = [page_size[1], page_size[0]]
            page['MediaBox'] = [0, 0] + page_size

        last_parent['Kids'].append(page.id)
        last_parent['Count'] += 1

        self.pages.append(page)
        self.n_page = self.page_count
        self.page_count += 1

    @property
    def page(self):
        return self.pages[self.n_page]

    def _build_pages_tree(self, page_parents):
        new_page_parents = []
        count = 0
        for page_parent in page_parents:
            if count % 6 == 0:
                new_page_parents.append(
                    self.base.add({'Type': b'/Pages', 'Kids': [], 'Count': 0})
                )
                count += 1

            last_parent = new_page_parents[-1]
            page_parent['Parent'] = last_parent.id
            last_parent['Kids'].append(page_parent.id)
            last_parent['Count'] += 1

        if count == 1:
            self.root['Pages'] = new_page_parents[0].id
            new_page_parents[0]['MediaBox'] = [0, 0] + self.page_size
        else:
            self._build_pages_tree(new_page_parents)


    def add_stream(self, instructions):
        graphic = self.base.add({'__stream__': instructions.encode('latin')})
        if not 'Contents' in self.page: self.page['Contents'] = []
        self.page['Contents'].append(graphic.id)
        

    def add_image(self, image_path, x, y, width, height):
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

    def add_text(self, content, d):
        pass
