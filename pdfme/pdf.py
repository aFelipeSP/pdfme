import copy

from .utils import get_page_size, subs, parse_margin, parse_style_str
from .standard_fonts import STANDARD_FONTS
from .base import PDFBase
from .image import PDFImage
from .text import PDFText
from .page import PDFPage
from .content import PDFContent

class PDF:
    def __init__(self, page_size='a4', portrait=True, margin=56.693,
        font_family='Helvetica',
        font_size=11,
        stroke_width=1,
        fill_color=0.1,
        stroke_color=0.1,
        text_align='l',
        line_height=1.1,
    ):

        self.page_width, self.page_height = get_page_size('a4')
        self.portrait = portrait

        self.margin = parse_margin(margin)

        self.width = self.page_width - self.margin['right'] - self.margin['left']
        self.height = self.page_height - self.margin['top'] - self.margin['bottom']

        self.font_family = font_family
        self.font_size = font_size
        self.stroke_width = stroke_width
        self.fill_color = fill_color
        self.stroke_color = stroke_color
        self.text_align = text_align
        self.line_height = line_height

        self.dests = {}

        self.pages = []
        self.page_count = 0

        self.base = PDFBase()
        self.root = self.base.add({ 'Type': b'/Catalog'})
        self.base.trailer['Root'] = self.root.id

        self.fonts = copy.deepcopy(STANDARD_FONTS)
        self.font_count = 6
        self.used_fonts = {}
        self._add_font('Helvetica', 'n')
        
        self.add_page()


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
        page = PDFPage(self.base)

        self.pages.append(page)
        self.n_page = self.page_count
        self.page_count += 1

        self.x = self.margin['left']
        self._y = self.page_height - self.margin['top']

        if ((page_size is None and portrait is None) or (page_size ==
            [self.page_width, self.page_height] and self.portrait == portrait)
        ): return

        page_size = [self.page_width, self.page_height] if page_size is None \
            else get_page_size(page_size)

        if (portrait is None and not self.portrait) or not portrait:
            page_size = [page_size[1], page_size[0]]

        # page.page['MediaBox'] = [0, 0] + page_size


    @property
    def page(self):
        return self.pages[self.n_page]


    def _build_pages_tree(self, page_list, first_level = True):
        new_page_list = []
        count = 0
        for page in page_list:
            if first_level:
                page = page.page

            if count % 6 == 0:
                new_page_list.append(
                    self.base.add({'Type': b'/Pages', 'Kids': [], 'Count': 0})
                )
                count += 1

            last_parent = new_page_list[-1]
            page['Parent'] = last_parent.id
            last_parent['Kids'].append(page.id)
            last_parent['Count'] += 1

        if count == 1:
            self.root['Pages'] = new_page_list[0].id

            page_size = [self.page_width, self.page_height] \
                if self.portrait else [self.page_height, self.page_width]

            new_page_list[0]['MediaBox'] = [0, 0] + page_size
        else:
            self._build_pages_tree(new_page_list, False)


    def stream(self, instructions):
        self.page.add(instructions)
        

    def create_image(self, image):
        return PDFImage(image)


    def add_image(self, pdf_image, width = None, height = None, move = 'bottom'):
        image_obj = self.base.add(pdf_image.pdf_obj)
        h = pdf_image.height
        w = pdf_image.width

        if width is None and height is None:
            width = self.width
            height = width * h/w
        elif width is None:
            width = height * w/h
        elif height is None:
            height = width * h/w

        self.page.add_image(image_obj, self.x, self._y - height, width, height)

        if move == 'bottom':
            self.move_y(height)
        if move == 'next':
            self.move_x(width)


    def image(self, image, width = None, height = None, move = 'bottom'):
        pdf_image = self.create_image(image)
        self.add_image(pdf_image, width, height, move)
       
    def _font_or_default(self, font_family, mode):
        return self.fonts[font_family]['n'] \
            if mode not in self.fonts[font_family] \
            else self.fonts[font_family][mode]

    def _add_font(self, font_family, mode):
        font = self._font_or_default(font_family, mode)

        font_obj = self.base.add({
            'Type': b'/Font',
            'Subtype': b'/Type1',
            'BaseFont': subs('/{}', font['base_font']),
            'Encoding': b'/WinAnsiEncoding'
        })
        self.used_fonts[(font_family, mode)] = font_obj
        return font_obj


    def _used_font(self, font_family, mode):
        font = self._font_or_default(font_family, mode)

        font_obj = self.used_fonts[(font_family, mode)] \
            if (font_family, mode) in self.used_fonts \
            else self._add_font(font_family, mode)

        self.page.add_font(font['ref'], font_obj.id)


    def default_text_style(self, width = None, height = None, text_align = None,
        line_height = None, indent = 0
    ):
        return dict(
            width = self.width + self.margin['left'] - self.x if width is None else width,
            height = self.height + self.margin['top'] - self.y if height is None else height,
            text_align = self.text_align if text_align is None else text_align,
            line_height = self.line_height if line_height is None else line_height,
            indent = indent
        )


    def init_content(self, content):
        style = {'f':self.font_family, 's':self.font_size, 'c':self.fill_color}
        if isinstance(content, str):
            content = {'style': style, '.': [content]}
        elif isinstance(content, (list, tuple)):
            content = {'style': style, '.': content}
        elif isinstance(content, dict):
            style_str = [key[1:] for key in content.keys() if key.startswith('.')]
            if len(style_str) > 0:
                style.update(parse_style_str(style_str[0], self.fonts))
            style.update(content.get('style', {}))
            content['style'] = style
        return content


    def create_text(self, content,
        width = None,
        height = None,
        text_align = None,
        line_height = None,
        indent = 0,
        list_text = None,
        list_indent = None,
        list_style = None
    ):
        par_style = self.default_text_style(width, height, text_align, line_height, indent)
        par_style.update({'list_text': list_text, 'list_indent': list_indent,
            'list_style': list_style})
        content = self.init_content(content)
        pdf_text = PDFText(content, self.fonts, **par_style)
        pdf_text.run()
        return pdf_text


    def add_text(self, pdf_text, move = 'bottom'):
        content = pdf_text.build(self.x, self._y)
        self.page.add(content)

        for font in pdf_text.used_fonts:
            self._used_font(*font)

        page_id = self.page.page.id
        for label, d in pdf_text.labels.items():
            self.dests[label] = [page_id, b'/XYZ', d['x'], d['y'],
                round(d['x']/self.page_width,3) + 1]

        for ref, rects in pdf_text.refs.items():
            for rect in rects:
                self.page.add_link(rect, ref)

        if move == 'bottom':
            self.move_y(pdf_text.current_height)
        if move == 'next':
            self.move_x(pdf_text.width)

        return pdf_text.remaining


    def text(self, content,
        width = None,
        height = None,
        text_align = None,
        line_height = None,
        indent = 0,
        list_text = None,
        list_indent = None,
        list_style = None,
        move = 'bottom'
    ):
        pdf_text = self.create_text(content, width, height, text_align,
            line_height, indent, list_text, list_indent, list_style)

        return self.add_text(pdf_text, move)

    
    def create_list(self, content,
        width = None,
        height = None,
        text_align = None,
        line_height = None,
        indent = 0,
        list_text = None,
        list_indent = None,
        list_style = None,
        list_start = 1,
        par_indent = 0,
        margin_bottom = 10
    ):

        pdf_list = {'par_indent': par_indent, 'margin_bottom': margin_bottom, 
            'list': [], 'remaining': None}

        par_style = self.default_text_style(width, height, text_align, line_height, indent)
        current_height = par_style['height']
        par_style['width'] -= par_indent

        for i, text in enumerate(content):
            if list_style == 'number':
                par_style['list_style'] = {'text': str(i+list_start)+'. '}
            else:
                if isinstance(list_style, dict):
                    par_style['list_style'] = list_style.copy()
                else:
                    par_style['list_style'] = list_style

            par_style['height'] = current_height

            text = self.init_content(text)
            pdf_text = PDFText(text, self.fonts, **par_style)
            pdf_text.run()

            current_height -= pdf_text.current_height + margin_bottom
            
            pdf_list['list'].append(pdf_text)

            if not pdf_text.remaining is None:
                remaining = content[i:]
                remaining[0] = pdf_text.remaining
                pdf_list['remaining'] = remaining
                break

        return pdf_list
        

    def add_list(self, pdf_list):
        self.move_x(pdf_list['par_indent'])

        for par in pdf_list['list']:
            self.add_text(par)
            self.move_y(pdf_list['margin_bottom'])

        return pdf_list['remaining']

    def list(self, content,
        width = None,
        height = None,
        text_align = None,
        line_height = None,
        indent = 0,
        style = None,
        list_style = 'disc',
        list_start = 1,
        par_indent = 0,
        margin_bottom = 10
    ):
        pdf_list = self.create_list(content, width, height, text_align, line_height,
            indent, style, list_style, list_start, par_indent, margin_bottom)

        return self.add_list(pdf_list)

    def _build_dests_tree(self, keys, vals, first_level=True):
        k = 7
        new_keys = []
        new_vals = []
        i = 0
        length = len(keys)
        obj = None
        count = 0

        while i < length:
            key = keys[i]
            val = vals[i]
            if i % k == 0:
                count += 1
                obj = self.base.add({})
                obj['Limits'] = [key if first_level else val[0], None]
                if first_level: obj['Names'] = []
                else: obj['Kids'] = []

            if first_level:
                obj['Names'].append(key)
                obj['Names'].append(val)
            else:
                obj['Kids'].append(key)

            if (i + 1) % k == 0 or (i + 1) == length:
                obj['Limits'][1] = key if first_level else val[1]
                new_keys.append(obj.id)
                new_vals.append(obj['Limits'])

            i += 1

        if count == 1:
            del obj['Limits']
            if not 'Names' in self.root: self.root['Names'] = {}
            self.root['Names']['Dests'] = obj.id
        else:
            self._build_dests_tree(new_keys, new_vals, False)


    def _build_dests(self):
        dests = list(self.dests.keys())
        if len(dests) == 0:
            return
        dests.sort()
        self._build_dests_tree(dests, [self.dests[k] for k in dests])

    def output(self, buffer):
        self._build_pages_tree(self.pages)
        self._build_dests()
        self.base.output(buffer)

    def add_content(self, content):
        pdf_content = PDFContent(content, self)
        pdf_content.run()
        # self.move_y(pdf_content.max_height)

        
