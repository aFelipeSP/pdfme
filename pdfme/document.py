from copy import deepcopy
from .pdf import PDF

STYLE_PROPS = dict(
    f='font_family', s='font_size', c='font_color',
    text_align='text_align', line_height='line_height'
)

PAGE_PROPS = ('page_size', 'portrait', 'margin')

def _set_running_sections(pdf, running_sections, defs):
    pdf.running_sections = []
    for name in running_sections:
        section = deepcopy(defs[name])

        if section.get('width') == 'left':
            section['width'] = pdf.margin['left']
        if section.get('width') == 'right':
            section['width'] = pdf.margin['right']
        if section.get('height') == 'top':
            section['height'] = pdf.margin['top']
        if section.get('height') == 'bottom':
            section['height'] = pdf.margin['bottom']
        if section.get('x') == 'left':
            section['x'] = pdf.margin['left']
        if section.get('x') == 'right':
            section['x'] = pdf.page_width - pdf.margin['right']
        if section.get('y') == 'top':
            section['y'] = pdf.margin['top']
        if section.get('y') == 'bottom':
            section['y'] = pdf.page_height - pdf.margin['bottom']

        pdf.running_sections.append(section)

def traverse_document_footnotes(element, footnotes, pdf):
    if isinstance(element, (list, tuple)):
        for child in element:
            traverse_document_footnotes(child, footnotes)
    elif isinstance(element, dict):
        if 'footnote' in element:
            element.setdefault('ids', [])
            name = '$footnote:' + str(len(footnotes))
            element['ids'].append(name)
            element['style'] = '$footnote'
            element['var'] = name
            pdf.context[name] = '0'
            footnotes.append(element['footnote'])
        else:
            for value in element.values():
                if isinstance(value, (list, tuple, dict)):
                    traverse_document_footnotes(value, footnotes, pdf)

def check_footnote(ids, pdf):
    for id_, rects in ids.items():
        if len(rects) == 0:
            continue
        if id_.startswith('$footnote:'):
            index = id_[10:]
           
def check_footnotes(section, pdf):
    # 
    pass
    # self.footnotes_height = 0
    # self.footnotes_ids.add(id_)
    # self.footnotes.append({'id': id_, 'content': content})
    # for footnote in self.footnotes:
    #     content = deepcopy(footnote['content'])
    #     content.setdefault('style', {}).setdefault('s', 10)
    #     pdf_text = self.pdf.create_text(footnote['content'],
    #         self.content_width, self.content_height,
    #         list_text=footnote['id'], list_indent=15,
    #         list_style={'r':0.5, 's': 6}
    #     )
    #     self.footnotes_height += pdf_text.current_height 

def build_pdf(document, buffer, context=None):
    style = document.get('style', {})
    style_props = {v: style[k] for k, v in STYLE_PROPS.items() if k in style}
    page_style = document.get('page_style', {})
    page_style = {p: page_style[p] for p in PAGE_PROPS if p in page_style}
    defs = document.get('defs', {})

    pdf = PDF(**page_style, **style_props)
    pdf.formats = document.get('formats', {})
    pdf.formats.setdefault('$footnote', {'r': 0.5})
    pdf.context.update(context)

    footnotes = []
    traverse_document_footnotes(document, footnotes, pdf)

    for section in document.get('sections', []):
        page_style = section.get('page_style', {})
        page_style = {p: page_style[p] for p in PAGE_PROPS if p in page_style}
        pdf.setup_page(**page_style)
        running_sections = section.get('running_sections', [])
        _set_running_sections(pdf, running_sections, defs)

        if 'page_numbering_offset' in page_style:
            pdf.page_numbering_offset = page_style['page_numbering_offset']
        if 'page_numbering_style' in page_style:
            pdf.page_numbering_style = page_style['page_numbering_style']
        if page_style.get('page_numbering_reset', False):
            pdf.page_numbering_offset = -len(pdf.pages)

        
        pdf.add_page()
        pdf_content = pdf._content(
            section, x=pdf.page.margin_left, width=pdf.page.content_width
        )
        pdf_content.parts_
        while not pdf_content.finished:
            pdf.add_page()
            pdf_content = pdf._content(pdf_content,
                pdf.page.content_width, pdf.page.content_height,
                pdf.page.margin_left, pdf.page.margin_top
            )

    pdf.output(buffer)


    def reset_added_footnotes(self):
        self.added_footnotes = set()

    def add_footnote(self, id_, content):
        if id_ in self.footnotes_ids:
            self.added_footnotes.add(id_)
            return False
        else:
            # add line before
            self.footnotes_height = 0
            self.footnotes_ids.add(id_)
            self.footnotes.append({'id': id_, 'content': content})
            for footnote in self.footnotes:
                content = deepcopy(footnote['content'])
                content.setdefault('style', {}).setdefault('s', 10)
                pdf_text = self.pdf.create_text(footnote['content'],
                    self.content_width, self.content_height,
                    list_text=footnote['id'], list_indent=15,
                    list_style={'r':0.5, 's': 6}
                )
                self.footnotes_height += pdf_text.current_height # add margin_bottom
        
            return True

    def end_page(self):
        self._y = self.margin_bottom + self.footnotes_height
        for footnote in self.footnotes:
            if footnote['id'] not in self.added_footnotes:
                continue

            content = deepcopy(footnote['content'])
            content.setdefault('style', {}).setdefault('s', 10)
            pdf_text = self.pdf.text(footnote['content'],
                self.content_width, self.content_height,
                list_text=footnote['id'], list_indent=15,
                list_style={'r':0.5, 's': 6}
            )