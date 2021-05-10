

class PDFPage:
    def __init__(self, base, width, height, margin_top=0, margin_bottom=0,
        margin_left=0, margin_right=0
    ):
        self.base = base
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right

        self.width = width
        self.height = height
        self.real_width = self.width - self.margin_right - self.margin_left
        self.real_height = self.height - self.margin_top - self.margin_bottom

        self.x = self.margin_left
        self._y = self.height - self.margin_top

        self.stream = base.add({'__stream__': b''})
        self.page = base.add({
            'Type': b'/Page', 'Contents': self.stream.id, 'Resources': {}
        })
        self.x_objects = set()

    @property
    def y(self):
        return self.height - self._y

    @y.setter
    def y(self, value):
        self._y = self.height - value

    def add(self, content):
        if isinstance(content, str):
            content = content.encode('latin')
        self.stream['__stream__'] += content

    def add_font(self, font_ref, font_obj_id):
        self.page['Resources'].setdefault('Font', {})
        if not font_ref in self.page['Resources']['Font']:
            self.page['Resources']['Font'][font_ref] = font_obj_id

    def add_link(self, rect, dest):
        if not 'Annots' in self.page: self.page['Annots'] = []
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
