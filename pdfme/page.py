

from copy import deepcopy


class PDFPage:
    def __init__(self, pdf, width, height, margin_top=0, margin_bottom=0,
        margin_left=0, margin_right=0
    ):
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right

        self.width = width
        self.height = height
        self.content_width = self.width - self.margin_right - self.margin_left
        self.content_height = self.height - self.margin_top - self.margin_bottom

        self.x = self.margin_left
        self._y = self.height - self.margin_top

        self.added_footnotes = set()
        self.footnotes_ids = set()
        self.footnotes = []

        self.stream = pdf.base.add({'__stream__': {}})
        self.page = pdf.base.add({
            'Type': b'/Page', 'Contents': self.stream.id, 'Resources': {}
        })
        self.x_objects = set()
        self.current_id = 0
        self.pdf = pdf

    @property
    def y(self):
        return self.height - self._y

    @y.setter
    def y(self, value):
        self._y = self.height - value

    def add(self, content):
        if isinstance(content, str):
            content = content.encode('latin')
        current_id = self.current_id
        self.stream['__stream__'][current_id] = content
        self.current_id += 1
        return current_id

    def add_font(self, font_ref, font_obj_id):
        self.page['Resources'].setdefault('Font', {})
        self.page['Resources']['Font'][font_ref] = font_obj_id

    def add_link(self, rect, uri_id):
        if not 'Annots' in self.page:
            self.page['Annots'] = []
        self.page['Annots'].append(
            {'Type': b'/Annot', 'Subtype': b'/Link', 'Rect': rect, 'A': uri_id}
        )

    def add_reference(self, rect, dest):
        if not 'Annots' in self.page:
            self.page['Annots'] = []
        self.page['Annots'].append(
            {'Type': b'/Annot', 'Subtype': b'/Link', 'Rect': rect, 'Dest': dest}
        )

    def add_image(self, image_obj, width, height):
        self.page['Resources'].setdefault('XObject', {})
        if not image_obj.id in self.x_objects:
            image_id = 'Im{}'.format(len(self.page['Resources']['XObject']))
            self.page['Resources']['XObject'][image_id] = image_obj.id
            self.x_objects.add(image_obj.id)

        self.add(' q {} 0 0 {} {} {} cm /{} Do Q'.format(round(width, 3),
            round(height, 3), round(self.x, 3), round(self._y, 3), image_id))

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
