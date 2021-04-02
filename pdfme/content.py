import copy

from .utils import parse_style_str

class PDFContent:
    def __init__(self, content, pdf,
        min_x=None, min_y=None, width=None, parent=None, max_y=None,
        last=False, inherited_style={}, page_content=None
    ):
        '''
        content: list of elements (dict) that will be added to the pdf. There are 
        currently 3 types of elements, defined by key 'type' in the element dict:
        - 'p' for paragraph element. It can have a 's' key (for 'style') for a dict
            specifying any of the following paragraph properties: 'text_align',
            'line_height', 'indent', 'list_style'.
        - 'i' for image element. The string in the 'i' key should contain the 
            path of the image to be added.
        - 'c' for content element. The list in the key 'c' can contain any of the
            other types of elements. It can have a 's' key (for 'style') for a dict
            specifying any properties that can be passed down to its children.

        All of the elements can have a 's' key holding a dict with any of the
        following keys to change the margin of the elements (or the children, in
        the case of 'c' type): 'margin-left', 'margin-top', 'margin-right',
        'margin-bottom', 
        '''

        self.page_content = {'content': []} if page_content is None else page_content
        self.pdf = pdf
        self.parent = parent
        self.root = parent is None
        self.last = last

        if not (isinstance(content, dict) and 'c' in content):
            content = {'c': [content]}

        self.original_style = {}
        self.original_style.update(inherited_style)
        self.original_style.update(content.get('style', {}))

        self.column = 0
        self.min_x = pdf.margin['left'] if min_x is None else min_x
        self.min_y = pdf.margin['top'] if min_y is None else min_y
        self.x = self.min_x
        self.y = self.min_y

        self.full_width = pdf.width if width is None else width
        self.max_y = pdf.height + pdf.margin['top'] if max_y is None else max_y
        self.max_height = self.max_y - self.y
        self.height = 0
        self.last_bottom = 0
        self.starting = True

        column_info = content.get('cols', {'count': 1, 'gap': 10})
        self.cols_n = column_info.get('count', 1)
        self.cols_gap = column_info.get('gap', 10)
        cols_spaces = self.cols_gap * (self.cols_n - 1)
        self.col_width = (self.full_width - cols_spaces) / self.cols_n

        self.elements = content.get('c')
        self.parent_last_element = 0 # variable to hold the index of the last time I have to call my parent to request a new parent section
        self.last_element = 0 # variable to hold the index of the last time I reached the end of a column
        self.delayed = [] # current delayed list
        self.last_delayed = [] # to save the delayed items got in the last time I request to my parent for a new section

        self.resetting = False
        self.content_index = len(self.page_content['content'])

        self.paragraph_properties = ('text_align', 'line_height', 'indent',
            'list_style')

    def add_delayed(self):
        '''Function to add delayed elements to pdf.

        This function will try to add the delayed elements to the pdf, and it can 
        return any of these strings:

        - 'continue' means caller could add all the delayed elements
        - 'break' means a parent element is reseting, and this instance must stop
        - 'next' means we need to move to the next section (column or page).
        '''

        is_last_element = len(self.elements) - 1 >= self.last_element
        n = len(self.delayed)

        while n:
            ret = self.process(self.delayed[0], is_last_element and n == 1)
            if ret is None: return 'break'
            if ret['delayed']: 
                self.delayed[0] = ret['delayed']
            else:
                self.delayed.pop(0)
                n -= 1
            if ret['next']: return 'next'

        return 'continue'

    def add_elements(self):
        '''Function to add elements to pdf.

        This function will try to add the elements to the pdf, and it can 
        return any of these strings:

        - 'continue' means caller could add all the elements
        - 'break' means a parent element is reseting, and this instance must stop
        - 'next' means we need to move to the next section (column or page).
        '''

        len_elems = len(self.elements) - 1
        for i in range(self.last_element, len_elems + 1):
            ret = self.process(self.elements[i], last=i == len_elems)
            if ret is None: return 'break'
            if ret['delayed']: self.delayed.append(ret['delayed'])
            if ret['next']:
                self.last_element = i + 1
                return 'next'

        return 'continue'
    
    # def update_adding_columns(self):
    #     if not self.resetting:
    #         self.y = self.min_y
    #     self.max_y = self.y if not self.resetting else self.max_y + 1

    def is_element_to_reset(self):
        if self.element_to_reset:
            self.reset()
            return 'reset'
        else:
            return 'break'

    def process_add_ans(self, ans):
        if ans == 'break':
            return self.is_element_to_reset()
        elif ans == 'next':
            should_continue = self.next_section()
            if not should_continue:
                return self.is_element_to_reset()
            else:
                return 'reset'


    def run(self):
        while True:
            action = self.process_add_ans(self.add_delayed())
            if action == 'break': return False
            elif action == 'reset': continue

            action = self.process_add_ans(self.add_elements())
            if action == 'break': return False
            elif action == 'reset': continue

            if not self.resetting and self.cols_n > 1:
                self.reset()
            else:
                if self.cols_n == 1:
                    self.max_height = self.height
                break

        if self.root and len(self.page_content['content']):
            self.build_page()
        
        return True

    def reset(self):
        self.page_content['content'] = self.page_content['content'][:self.content_index]
        self.go_to_beggining()
        self.max_y = self.y + 10 if not self.resetting else self.max_y + 10
        self.resetting = True
        self.last_element = self.parent_last_element
        self.delayed = copy.deepcopy(self.last_delayed)

    def go_to_beggining(self):
        self.y = self.min_y
        self.x = self.min_x
        self.column = 0

    def next_section(self, direct=True):
        """Goes to the new section of the pdf document.

        It can be called by current node or by a child node.
        When called by current node it returns:
        - True if it's safe to continue.
        - False if it should break because a parent is resetting, and this
          child should end its processing.
        When called by child node it returns the new min_x and min_y in a dict or
        None if a parent has said original caller should initiate a chain reaction
        to break all the elements upwards until it get to the parent (the one that 
        has the attribute current_element_ended) that should reset.
        """

        # TODO: modify self.content_index after my parent added a new section


        if self.column == self.cols_n - 1:
            if self.resetting:
                self.element_to_reset = True
                return None
            elif self.root:
                self.build_page()
                self.pdf.add_page()
                self.min_x = self.pdf.margin['left']
                self.min_y = self.pdf.margin['top']
                self.go_to_beggining()
                self.parent_last_element = self.last_element
                self.last_delayed = self.delayed
                return True if direct else \
                    {'min_x': self.min_x, 'min_y': self.min_y}
            else:
                ret = self.parent.next_section(False)
                if ret is None:
                    return False if direct else None
                self.min_y = ret['min_y']
                self.min_x = ret['min_x']
                self.content_index = len(self.page_content['content'])
                self.go_to_beggining()
                self.parent_last_element = self.last_element
                self.last_delayed = copy.deepcopy(self.delayed)
                return True if direct else ret
        else:
            self.column += 1

            self.y = self.min_y
            self.update_dimensions()
            return True if direct else \
                {'min_x': self.get_min_x(), 'min_y': self.min_y}

    def get_min_x(self):
        return self.min_x + self.column * (self.col_width + self.cols_gap)

    def build_page(self):
        for part in self.page_content['content']:
            self.pdf.x = part['x']; self.pdf.y = part['y']
            if part['type'] == 'p':
                self.pdf.add_text(part['content'])
            elif part['type'] == 'i':
                self.pdf.add_image(part['content'], part['width'])

        self.content_index = 0
        self.page_content['content'] = []

    def move_y(self, h):
        self.height += h
        self.y += h

    def update_dimensions(self):
        s = self.style
        self.x = self.get_min_x() + s.get('margin-left', 0)

        self.width = self.col_width - s.get('margin-left', 0) - s.get('margin-right', 0)
        
        if self.starting:
            self.starting = False
        else:
            self.move_y(self.last_bottom + s.get('margin-top', 0))

        self.max_height = self.max_y - self.y
        self.last_bottom = s.get('margin-bottom', 0)


    def process(self, element, last=False):
        '''Function to add a single element to the pdf

        This function will add an element to the pdf, using the method
        corresponding to the type of the object (text, image, or another content).
        If some parent element is resetting, it will return None. Else, 
        a dict with 2 keys:

        - delayed: if not None, it will contain an element that should be added
        by the caller function in the next section, because it didn't fit in
        the current section.

        - next: if True, the caller function should go to the next section of
        the pdf.
        '''

        if isinstance(element, (str, list, tuple)):
            element = {'p': element}

        if not isinstance(element, dict):
            raise TypeError('Elements must be of type dict, str, list or tuple:' + 
                str(element))

        self.style = {}
        self.style.update(self.original_style)
        # it was decided that the styles in content are always objects, not strings
        el_style = element.get('s', {})
        if isinstance(el_style, dict):
            self.style.update(el_style)

        self.update_dimensions()
        content = {'x': self.x, 'y': self.y}
        ret =  {'delayed': None, 'next': False}

        if 'p' in element:
            par_style = {
                v: self.style.get(v) for v in self.paragraph_properties
                if self.style.get(v) is not None
            }
            pdf_text = self.pdf.create_text(element['p'], width = self.width, 
                height = self.max_height, **par_style)
            content.update({'type': 'p', 'content': pdf_text})
            self.page_content['content'].append(content)

            self.move_y(pdf_text.current_height)
            if pdf_text.remaining is not None:
                ret = {'delayed': pdf_text.remaining, 'next': True}

        elif 'i' in element:
            pdf_image = self.pdf.create_image(element['i'])
            height = self.width * pdf_image.height/pdf_image.width

            if height < self.max_height:
                content.update({'type': 'i', 'width': self.width,
                    'height': height, 'content': pdf_image})
                self.page_content['content'].append(content)
                self.move_y(height)
            else:
                image_place = self.style.get('image_place', 'flow')
                ret['delayed'] = element['i']
                if image_place == 'normal':
                    ret['next'] = True
                # elif image_place == 'flow':
                #     ret['next'] = False

        # elif 'r' in element:
        #     self.pdf.table()

        elif 'c' in element:
            pdf_content = PDFContent(element, self.pdf, min_x=self.get_min_x(),
                min_y=self.y, width=self.col_width, parent=self, 
                max_y=self.max_y, last=last, inherited_style=copy.deepcopy(self.style),
                page_content=self.page_content)
            
            # check what should be returned here
            should_continue = pdf_content.run()
            if not should_continue:
                ret = None
            self.move_y(pdf_content.max_height)

        return ret