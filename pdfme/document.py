from copy import deepcopy
from .pdf import PDF

STYLE_PROPERTIES = dict(f='font_family', s='font_size', c='font_color',
            text_align='text_align', line_height='line_height')

PAGE_PROPERTIES = ('page_size', 'portrait', 'margin')

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

def build_pdf(document, buffer, context=None):
    style = document.get('style', {})

    style_props = {
        prop: style[key] for key, prop in STYLE_PROPERTIES.items()
        if key in style
    }

    page_style = document.get('page_style', {})
    defs = document.get('defs', {})

    pdf = PDF(**page_style, **style_props)
    pdf.formats = document.get('formats', {})
    pdf.context.update(context)

    for section in document.get('sections', []):
        section_page_style = section.get('page_style', {})
        pdf.setup_page(**{
            prop: section_page_style[prop] for prop in PAGE_PROPERTIES
            if prop in section_page_style
        })

        running_sections = section.get('running_sections', [])
        _set_running_sections(pdf, running_sections, defs)

        if 'page_numbering_offset' in section_page_style:
            pdf.page_numbering_offset = section_page_style['page_numbering_offset']
        if 'page_numbering_style' in section_page_style:
            pdf.page_numbering_style = section_page_style['page_numbering_style']
        if section_page_style.get('page_numbering_reset', False):
            pdf.page_numbering_offset = -len(pdf.pages)

        pdf.add_page()
        pdf.content(section)

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