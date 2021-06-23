from copy import deepcopy
from .pdf import PDF

STYLE_PROPS = dict(
    f='font_family', s='font_size', c='font_color',
    text_align='text_align', line_height='line_height'
)

PAGE_PROPS = ('page_size', 'portrait', 'margin')

class PDFDocument:
    def __init__(self, document, context=None):
        context = {} if context is None else context
        style = deepcopy(document.get('style', {}))
        style_args = {
            v: style.pop(k) for k, v in STYLE_PROPS.items() if k in style
        }
        page_style = document.get('page_style', {})
        page_args = {p: page_style[p] for p in PAGE_PROPS if p in page_style}

        self.pdf = PDF(**page_args, **style_args)
        self.pdf.formats = {}
        self.pdf.formats['$footnote'] = {'r': 0.5, 's': 6}
        self.pdf.formats['$footnotes'] = {'s': 10, 'c': 0}
        self.pdf.formats.update(document.get('formats', {}))
        self.pdf.context.update(context)

        self.defs = document.get('defs', {})
        self.style = style

        self.sections = document.get('sections', [])

        self.footnotes = []
        self.traverse_document_footnotes(self.sections)

        self.footnotes_margin = 10

    def traverse_document_footnotes(self, element):
        if isinstance(element, (list, tuple)):
            for child in element:
                self.traverse_document_footnotes(child)
        elif isinstance(element, dict):
            if 'footnote' in element:
                element.setdefault('ids', [])
                name = '$footnote:' + str(len(self.footnotes))
                element['ids'].append(name)
                element['style'] = '$footnote'
                element['var'] = name
                self.pdf.context[name] = '0'

                footnote = element['footnote']

                if not isinstance(footnote, (dict, str, list, tuple)):
                    footnote = str(footnote)
                if isinstance(footnote, (str, list, tuple)):
                    footnote = {'.': footnote}

                if not isinstance(footnote, dict):
                    raise TypeError(
                        'footnotes must be of type dict, str, list or tuple:{}'
                        .format(footnote)
                    )

                self.footnotes.append(footnote)
            else:
                for value in element.values():
                    if isinstance(value, (list, tuple, dict)):
                        self.traverse_document_footnotes(value)

    def set_running_sections(self, running_sections):
        self.pdf.running_sections = []
        for name in running_sections:
            section = deepcopy(self.defs[name])
            margin = self.pdf.margin
            if section.get('width') in ['left', 'right']:
                section['width'] = margin[section.get('width')]
            if section.get('width') == 'full':
                section['width'] = self.pdf.page_width
            if section.get('height') in ['top', 'bottom']:
                section['height'] = margin[section.get('height')]
            if section.get('height') == 'full':
                section['height'] = self.pdf.page_height
            if section.get('x') == 'left':
                section['x'] = margin['left']
            if section.get('x') == 'right':
                section['x'] = self.pdf.page_width - margin['right']
            if section.get('y') == 'top':
                section['y'] = margin['top']
            if section.get('y') == 'bottom':
                section['y'] = self.pdf.page_height - margin['bottom']

            width = section.get('width', (
                self.pdf.page_width - margin['right'] - margin['left']
            ))
            height = section.get('height', (
                self.pdf.page_height - margin['top'] - margin['bottom']
            ))
            x = section.get('x', 0)
            y = section.get('y', 0)
            self.pdf.add_running_section(section, width, height, x, y)

    def run(self):
        for section in self.sections:
            self.process_section(section)

    def process_section(self, section):
        page_style = section.get('page_style', {})
        page_args = {p: page_style[p] for p in PAGE_PROPS if p in page_style}
        self.pdf.setup_page(**page_args)
        running_sections = section.get('running_sections', [])
        self.set_running_sections(running_sections)

        pdf = self.pdf
        self.width = pdf.page_width - pdf.margin['right'] - pdf.margin['left']
        self.y = pdf.page_height - pdf.margin['top']
        self.height = self.y - pdf.margin['bottom']
        self.x = pdf.margin['left']

        if 'page_numbering_offset' in page_style:
            self.pdf.page_numbering_offset = page_style['page_numbering_offset']
        if 'page_numbering_style' in page_style:
            self.pdf.page_numbering_style = page_style['page_numbering_style']
        if page_style.get('page_numbering_reset', False):
            self.pdf.page_numbering_offset = -len(self.pdf.pages)

        self.section = self.pdf._create_content(
            section, self.width, self.height, self.x, self.y
        )

        self.add_pages()

    def add_pages(self):
        while not self.section.finished:
            self.add_page()

    def add_page(self):
        self.pdf.add_page()
        content_part = self.section.pdf_content_part
        first_page = content_part is None
        if first_page:
            section_element_index = 0
            section_delayed = []
            children_indexes = []
        else:
            section_element_index = deepcopy(content_part.section_element_index)
            section_delayed = deepcopy(content_part.section_delayed)
            children_indexes = deepcopy(content_part.children_indexes)
        
        self.section.run(height=self.height)
        if first_page:
            content_part = self.section.pdf_content_part
        footnotes_obj = self.process_footnotes()

        if footnotes_obj is None:
            self.pdf._add_graphics([*self.section.fills,*self.section.lines])
            self.pdf._add_parts(self.section.parts)
            self.pdf.page._y -= self.section.current_height
        else:
            footnotes_height = footnotes_obj.current_height
            if footnotes_height >= self.height - self.footnotes_margin - 20:
                raise Exception(
                    "footnotes are very large and don't fit in one page"
                )
            new_height = self.height - footnotes_obj.current_height \
                - self.footnotes_margin
            
            content_part.section_element_index = section_element_index
            content_part.section_delayed = section_delayed
            content_part.children_indexes = children_indexes

            self.pdf._content(self.section, height=new_height)

            footnotes_obj = self.process_footnotes()
            
            if footnotes_obj is not None:
                self.pdf.page._y = self.pdf.margin['bottom'] + footnotes_height

                x_line = round(self.pdf.page.x, 3)
                y_line = round(self.pdf.page._y + self.footnotes_margin/2, 3)
                self.pdf.page.add(' q 0 G 0.5 w {} {} m {} {} l S Q'.format(
                    x_line, y_line, x_line + 150, y_line
                ))
                self.pdf._content(footnotes_obj, height=self.height)

    def check_footnote(self, ids, page_footnotes):
        for id_, rects in ids.items():
            if len(rects) == 0:
                continue
            if id_.startswith('$footnote:'):
                index = int(id_[10:])
                page_footnotes.append(self.footnotes[index])
                self.pdf.context[id_] = len(page_footnotes)

    def check_footnotes(self, page_footnotes):
        for part in self.section.parts:
            if part['type'] == 'paragraph':
                self.check_footnote(part['ids'], page_footnotes)
        
    def get_footnotes_obj(self, page_footnotes):
        content = {'style': '$footnotes', 'content': []}
        for index, footnote in enumerate(page_footnotes):
            footnote = deepcopy(footnote)
            style = footnote.setdefault('style', {})
            style.update(dict(list_text=index + 1, list_style='$footnote'))
            content['content'].append(footnote)

        footnote_obj = self.pdf._create_content(
            content, self.width, self.height, self.x, self.y
        )
        footnote_obj.run()
        return footnote_obj
    
    def process_footnotes(self):
        page_footnotes = []
        self.check_footnotes(page_footnotes)
        if len(page_footnotes) == 0:
            return None
        return self.get_footnotes_obj(page_footnotes)

    def output(self, buffer):
        self.pdf.output(buffer)

def build_pdf(document, buffer, context=None):
    doc = PDFDocument(document, context)
    doc.run()
    doc.output(buffer)