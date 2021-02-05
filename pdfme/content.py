import copy

from .utils import parse_style_str

class PDFContent:
    def __init__(self, content, pdf, min_x=None, min_y=None, width=None, parent=None, max_y=None, last=False, inherited_style={}, page_content=None):

        self.page_content = {'content': []} if page_content is None else page_content
        self.root = page_content is None

        self.pdf = pdf
        self.parent = parent
        self.last = last

        if not (isinstance(content, dict) and 'c' in content):
            content = {'c': [content]}

        self.original_style = {}
        self.original_style.update(inherited_style)
        self.original_style.update(content.get('style'))

        self.column = 0
        self.min_x = pdf.margin['left'] if min_x is None else min_x
        self.min_y = pdf.margin['top'] if min_y is None else min_y
        self.x = self.min_x
        self.y = self.min_y

        self.full_width = pdf.width if width is None else width
        self.max_y = pdf.height + pdf.margin['top'] if max_y is None else max_y
        self.height = self.max_y - self.y
        self.last_bottom = 0
        self.starting = True
        self.delayed = []

        column_info = content.get('cols', {'count': 1, 'gap': 0})
        self.cols_n = column_info.get('count', 1)
        self.cols_gap = column_info.get('gap', 0)
        cols_spaces = self.cols_gap * (self.cols_n - 1)
        self.col_width = (self.full_width - cols_spaces) / self.cols_n

        self.remaining = None

        self.elements = content.get('c')
        self.current_delayed = 0
        self.current_element = 0

        self.run()
    
    def run(self):
        n_delayed = len(self.delayed)
        for i in range(self.current_delayed, n_delayed):
            ret = self.process(self.current_delayed[i])
            if ret:
                self.current_delayed = i + 1


        n_elems = len(self.elements) - 1
        for i in range(self.current_element, n_elems + 1):
            ret = self.process(self.elements[i], i == n_elems)
            if ret:
                self.current_element = i + 1
                self.run()
                return
                
        self.child_ended()

    def child_ended(self):
        if not self.parent is None and self.parent.cols_n > 1 and self.last:
            self.parent.child_ended()
        else:
            self.ended()

    def ended(self):

        # calculate the amount of height to accomodate whathever there is in this element and its children
        # Repeat the process, adding some height to first column if necessary, to accomodate all the content
        # this could be achieved by using a minimizer, and using the maximum height of the columns as the minimization objective

        self.height

    def next_section(self):
        self.add_page()
        if self.column == self.cols_n - 1:
            if self.root:

                self.pdf.add_page()
                self.y = self.min_y
            else:
                self.column = 0
                res = self.parent.next_section()
                # TODO: apply res dimmensions to this instance
                return res
        else:
            self.column += 1

            self.y = self.min_y
            self.starting = True
            self.update_dimensions()

    def add_page(self):
        for part in self.page_content['content']:
            self.pdf.x = part['x']; self.pdf.y = part['y']
            if part['type'] == 't':
                self.pdf.add_text(part['content'])
            elif part['type'] == 'i':
                self.pdf.add_image(part['content'], part['width'])

        self.page_content['content'] = []

    def update_dimensions(self):
        s = self.style
        self.x = self.min_x + self.column * (
            self.col_width + self.cols_gap) + s.get('margin-left', 0)

        self.width = self.col_width - s.get('margin-left', 0) - s.get('margin-right', 0)
        
        if self.starting:
            self.starting = False
        else:
            self.y += self.last_bottom + s.get('margin-top', 0)

        self.height = self.max_y - self.y
        self.last_bottom = s.get('margin-bottom', 0)

    def create_content(self, content, type_, height):
        return {'x': self.x, 'y': self.y, 'type': type_, 'height': height ,
            'content': content}


    def process(self, element, last=False):

        if isinstance(element, (str, list, tuple)):
            element = {'t': element}

        if not isinstance(element, dict):
            raise TypeError('Elements must be of type dict, list or str:' + 
                str(element))

        self.style = {}
        self.style.update(self.original_style)
        self.style.update(element.get('s', {}))

        self.update_dimensions()

        if 't' in element:
            pdf_text = self.pdf.create_text(element, width = self.width, 
                height = self.height, **{v: self.style.get(v) for v in [
                'text_align', 'line_height', 'indent', 'list_style']})
            content = {'x': self.x, 'y': self.y, 'type': 't',
                'height': pdf_text.current_height ,'content': pdf_text}
            self.page_content['content'].append(content)

            self.y += pdf_text.current_height

            if not pdf_text.remaining is None:
                self.delayed.append(pdf_text.remaining)
                self.next_section()
                return True

        elif 'i' in element:
            pdf_image = self.pdf.create_image(element['i'])
            height = self.width * pdf_image.height/pdf_image.width

            if height < self.height:
                self.page_content['content'].append({'x': self.x, 'y': self.y,
                    'type': 'i', 'width': self.width, 'height': height,
                    'content': pdf_image})
                self.y += height
            else:
                image_place = self.style.get('image_place')
                self.delayed.append(pdf_image)
                if image_place is None or image_place == 'normal':
                    self.next_section()
                    return True

        # elif 'r' in element:
        #     self.pdf.table()

        elif 'c' in element:
            pdf_content = PDFContent(element, self.pdf, min_x=self.min_x,
                min_y=self.pdf.y, width=self.col_width, parent=self, 
                max_y=self.max_y, last=last, inherited_style=copy.deepcopy(self.style),
                page_content=self.page_content)

            self.x = self.min_x
            self.y = pdf_content.y

        return False