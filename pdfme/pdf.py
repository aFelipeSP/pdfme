import copy

from .utils import (get_page_size, subs, parse_margin, parse_style_str,
    create_graphics, to_roman
)
from .standard_fonts import STANDARD_FONTS
from .base import PDFBase
from .image import PDFImage
from .text import PDFText
from .page import PDFPage
from .content import PDFContent
from .table import PDFTable

class PDF:
    def __init__(self, page_size='a4', portrait=True, margin=56.693,
        page_numbering_offset=0, page_numbering_style='arabic',
        font_family='Helvetica', font_size=11, font_color=0.1,
        text_align='l', line_height=1.1
    ):

        self.setup_page(page_size, portrait, margin)
        self.page_numbering_offset = page_numbering_offset
        self.page_numbering_style = page_numbering_style

        self.font_family = font_family
        self.font_size = font_size
        self.font_color = font_color
        self.text_align = text_align
        self.line_height = line_height

        self.dests = {}
        self.pages = []
        self.running_sections = []

        self.base = PDFBase()
        self.root = self.base.add({ 'Type': b'/Catalog'})
        self.base.trailer['Root'] = self.root.id

        self.fonts = copy.deepcopy(STANDARD_FONTS)
        self.used_fonts = {}
        self._add_font('Helvetica', 'n')

    @property
    def page(self):
        return self.pages[self.page_index]

    def setup_page(self, page_size=None, portrait=None, margin=None):
        if page_size is not None:
            self.page_width, self.page_height = get_page_size(page_size)
        if portrait is not None:
            self.portrait = portrait
        if margin is not None:
            self.margin = parse_margin(margin)

    def add_page(self, page_size=None, portrait=None, margin=None):
        if page_size is not None:
            page_width, page_height = get_page_size(page_size)
        else:
            page_height, page_width = self.page_height, self.page_width

        if (portrait is None and not self.portrait) or not portrait:
            page_height, page_width = page_width, page_height  

        margin_ = copy.deepcopy(self.margin)
        if margin is not None:
            margin_.update(parse_margin(margin))

        page = PDFPage(self.base, page_width, page_height,
            **{'border_' + side: value for side, value in margin_.items()}
        )

        self.pages.append(page)
        self.page_index = len(self.pages) - 1

        for running_section in self.running_sections:
            self._content(**running_section)

    def add_running_section(self, name, content, width=None, height=None,
        x=None, y=None, context=None
    ):
        self.running_sections.append(dict(content=content, width=width,
            height=height, x=x, y=y, context=context
        ))

    def create_image(self, image):
        return PDFImage(image)

    def add_image(self, pdf_image, x=None, y=None, width=None, height=None,
        move='bottom'
    ):
        image_obj = self.base.add(pdf_image.pdf_obj)
        h = pdf_image.height
        w = pdf_image.width

        if width is None and height is None:
            width = self.page.content_width
            height = width * h/w
        elif width is None:
            width = height * w/h
        elif height is None:
            height = width * h/w

        if x is not None:
            self.page.x = x
        if y is not None:
            self.page.y = y

        self.page.add_image(image_obj, width, height)

        if move == 'bottom':
            self.page.y += height
        if move == 'next':
            self.page.x += width

    def image(self, image, width=None, height=None, move='bottom'):
        pdf_image = self.create_image(image)
        self.add_image(pdf_image, width=width, height=height, move=move)

    def add_font(self, font_family, font_files):
        raise NotImplementedError()
       
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

    def _default_paragraph_style(self, width=None, height=None, text_align=None,
        line_height=None, indent=0
    ):
        return dict(
            width = self.page.width - self.page.margin_right - self.page.x \
                if width is None else width,
            height = self.page.height - self.page.margin_bottom - self.page.y \
                if height is None else height,
            text_align = self.text_align if text_align is None else text_align,
            line_height = self.line_height if line_height is None \
                else line_height,
            indent = indent
        )

    def _init_text(self, content):
        style = {'f': self.font_family, 's': self.font_size, 'c': self.font_color}
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

    def get_page_number(self):
        page = self.page_index + 1 + self.page_numbering_offset
        return to_roman(page) if self.page_numbering_style == 'roman' else page

    def _default_context(self, context):
        if isinstance(context, dict):
            context = copy.deepcopy(context)
            context['_PAGE_'] = self.get_page_number()
        else:
            raise Exception('context must be a dict')
        return context

    def create_text(self, content, width=None, height=None, text_align=None,
        line_height=None, indent=0, list_text=None, list_indent=None,
        list_style = None, context=None
    ):
        par_style = self._default_paragraph_style(width, height, text_align,
            line_height, indent)
        par_style.update({'list_text': list_text, 'list_indent': list_indent,
            'list_style': list_style})
        content = self._init_text(content)
        context = self._default_context(context)
        pdf_text = PDFText(content, self.fonts, context=context, **par_style)
        pdf_text.run()
        return pdf_text

    def add_text(self, pdf_text, x=None, y=None, move='bottom'):
        if x is not None:
            self.page.x = x
        if y is not None:
            self.page.y = y

        content = pdf_text.build(self.page.x, self.page._y)
        self.page.add(content)

        for font in pdf_text.used_fonts:
            self._used_font(*font)

        page_id = self.page.page.id
        for label, d in pdf_text.labels.items():
            self.dests[label] = [page_id, b'/XYZ', d['x'], d['y'],
                round(d['x']/self.page.width, 3) + 1]

        for ref, rects in pdf_text.refs.items():
            for rect in rects:
                self.page.add_link(rect, ref)

        if move == 'bottom':
            self.page.y += pdf_text.current_height
        if move == 'next':
            self.page.x += pdf_text.width

        return pdf_text.remaining

    def text(self, content, x=None, y=None, width=None, height=None,
        text_align=None, line_height=None, indent=0, list_text=None,
        list_indent=None, list_style=None, context=None, move='bottom'
    ):
        pdf_text = self.create_text(content, width, height, text_align,
            line_height, indent, list_text, list_indent, list_style, context)

        return self.add_text(pdf_text, x, y, move)

    def _position_and_size(self, x=None, y=None, width=None, height=None):
        if x is not None:
            self.page.x = x
        if y is not None:
            self.page.y = y
        if width is None:
            width = self.page.width - self.page.margin_right - self.page.x
        if height is None:
            height = self.page.height - self.page.margin_bottom - self.page.y
        return x, y, width, height

    def _default_content_style(self):
        return dict(f=self.font_family, s=self.font_size, c=self.font_color,
            text_align=self.text_align, line_height=self.line_height, indent=0
        )

    def _create_table(self, content, width=None, height=None, x=None, y=None,
        widths=None, style=None, borders=None, fills=None,
        context=None
    ):
        style_ = self._default_content_style()
        if isinstance(style, dict):
            style_.update(style)
        
        context = self._default_context(context)
        pdf_table = PDFTable(content, self.fonts, width, height, x, y,
            widths, style_, borders, fills, context)
        pdf_table.run()
        return pdf_table

    def _table(self, content, width=None, height=None, x=None, y=None,
        widths=None, style=None, borders=None, fills=None,
        context=None, move='bottom'
    ):
        x, y, width, height = self._position_and_size(x, y, width, height)

        if isinstance(content, PDFTable):
            pdf_table = content
            if isinstance(context, dict):
                pdf_table.context.update(context)
            pdf_table.context['_PAGE_'] = self.get_page_number()
            pdf_table.setup(x, y, width, height)
            pdf_table.run()
        else:
            pdf_table = self._create_table(content, width, height, x, y,
                widths, style, borders, fills, context
            )

        self._add_graphics([*pdf_table.fills,*pdf_table.lines])
        self._add_parts(pdf_table.parts_)

        if move == 'bottom':
            self.page.y += pdf_table.current_height
        if move == 'next':
            self.page.x += width

        return pdf_table

    def table(self, content, widths=None, style=None, borders=None,
        fills=None, context=None
    ):
        pdf_table = self._table(content, widths=widths, style=style,
            borders=borders, fills=fills, context=context,
            x=self.page.margin_left, width=self.page.content_width
        )
        while not pdf_table.finished:
            self.add_page()
            pdf_table = self._content(pdf_table,
                self.page.content_width, self.page.content_height,
                self.page.margin_left, self.page.margin_top
            )

    def _create_content(self, content, width=None, height=None, x=None, y=None,
        context=None
    ):
        style = self._default_content_style()

        content = content.copy()
        style.update(content.get('style', {}))
        content['style'] = style

        context = self._default_context(context)
        pdf_content = PDFContent(content, width, height, x, y, context)
        pdf_content.run()
        return pdf_content

    def _content(self, content, width=None, height=None, x=None, y=None,
        context=None, move='bottom'
    ):
        x, y, width, height = self._position_and_size(x, y, width, height)

        if isinstance(content, PDFContent):
            pdf_content = content
            if isinstance(context, dict):
                pdf_content.context.update(context)
            pdf_content.context['_PAGE_'] = self.get_page_number()
            pdf_content.setup(x, y, width, height)
            pdf_content.run()
        else:
            pdf_content = self._create_content(content, width, height,
                x, y, context)

        self._add_graphics([*pdf_content.fills,*pdf_content.lines])
        self._add_parts(pdf_content.parts_)

        if move == 'bottom':
            self.page.y += pdf_content.current_height
        if move == 'next':
            self.page.x += width

        return pdf_content

    def content(self, content, context=None):
        pdf_content = self._content(content, context=context,
            x=self.page.margin_left, width=self.page.content_width)
        while not pdf_content.finished:
            self.add_page()
            pdf_content = self._content(pdf_content,
                self.page.content_width, self.page.content_height,
                self.page.margin_left, self.page.margin_top
            )

    def _add_graphics(self, graphics):
        stream = create_graphics(graphics)
        self.page.add(stream)

    def _add_parts(self, parts):
        for part in parts:
            self.page.x = part['x']; self.page.y = part['y']
            if part['type'] == 'paragraph':
                self.add_text(part['content'])
            elif part['type'] == 'image':
                self.add_image(part['content'], part['width'])

    def _build_pages_tree(self, page_list, first_level = True):
        new_page_list = []
        count = 0
        for page in page_list:
            if first_level:
                page = page.page
                page_size = [page.width, page.height]
                page['MediaBox'] = [0, 0] + page_size

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
        else:
            self._build_pages_tree(new_page_list, False)

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
