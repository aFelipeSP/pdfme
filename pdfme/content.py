import copy

from .utils import parse_style_str


class PDFContent:
    def __init__(self, content, pdf, min_x=None, width=None, min_y=None, max_y=None):
        self.page = []
        self.pdf = pdf
        self.content = content
        self.min_x = pdf.margin['left'] if min_x is None else min_x
        self.min_y = pdf.margin['top'] if min_y is None else min_y

        self.width = pdf.width if width is None else width
        self.max_y = pdf.height + pdf.margin['top'] if max_y is None else max_y

    def build_page(self):
        for part in self.page:
            self.pdf.x = part['x']; self.pdf.y = part['y']
            if part['type'] == 'paragraph':
                self.pdf.add_text(part['content'])
            elif part['type'] == 'image':
                self.pdf.add_image(part['content'], part['width'])

        self.page = []

    def run(self):
        top = self.pdf.margin['top']
        pdf_content_part = PDFContentPart(self.content, self,
            self.min_x, self.width, self.min_y, self.max_y, last=True
        )
        pdf_content_part.run()

class PDFContentPart:
    def __init__(self, content, pdf_content, min_x, width, min_y, max_y,
        parent=None, last=False, inherited_style=None
    ):
        '''
        content: list of elements (dict) that will be added to the pdf. There are
        currently 3 types of elements, defined by key 'type' in the element dict:
        - '.*' for paragraph element. It can have a 'style' key for a dict
            specifying any of the following paragraph properties: 'text_align',
            'line_height', 'indent', 'list_text', 'list_indent', 'list_style'.
        - 'image' for image element. The string in the 'image' key should contain the
            path of the image to be added.
        - 'content' for content element. The list in the key 'content' can contain any of the
            other types of elements. It can have a 'style' key for a dict
            specifying any properties that can be passed down to its children.

        All of the elements can have a 'style' key holding a dict with any of the
        following keys to change the margin of the elements (or the children, in
        the case of 'content' type): 'margin_left', 'margin_top', 'margin_right',
        'margin_bottom',
        '''

        self.p = pdf_content
        self.parent = parent
        self.is_root = parent is None
        self.last = last

        self.style = {'margin_bottom': 5}
        inherited_style = {} if inherited_style is None else inherited_style
        self.style.update(inherited_style)
        self.style.update(content.get('style', {}))

        self.min_x = min_x
        self.min_y = min_y
        self.go_to_beggining()

        self.full_width = width
        self.max_y = max_y
        self.max_height = self.max_y - self.y
        self.height = 0
        self.last_bottom = 0
        self.starting = True

        column_info = content.get('cols', {'count': 1, 'gap': 10})

        if not isinstance(column_info, dict):
            raise TypeError('column_info must be a dict:'.format(column_info))

        self.cols_n = column_info.get('count', 1)
        self.cols_gap = column_info.get('gap', 10)
        cols_spaces = self.cols_gap * (self.cols_n - 1)
        self.col_width = (self.full_width - cols_spaces) / self.cols_n

        self.elements = content.get('content')

        self.section_element_index = 0 # index when the last section jump occured
        self.element_index = 0 # current index

        self.section_delayed = [] # delayed elements when the last section jump occured
        self.delayed = [] # current delayed elements

        self.children_indexes = [] # the last state of this element

        self.will_reset = False
        self.resetting = False
        self.page_index = len(self.p.page)

        self.minim_diff_last = None
        self.minim_diff = None
        self.minim_forward = None

        self.paragraph_properties = ('text_align', 'line_height', 'indent',
            'list_text', 'list_style', 'list_indent')

    def add_delayed(self):
        '''Function to add delayed elements to pdf.

        This function will try to add the delayed elements to the pdf, and it can
        return any of these strings:

        - 'continue' means caller could add all the delayed elements
        - 'break' means a parent element is reseting, and this instance must stop
        - 'next' means we need to move to the next section (column or page).
        '''
        n = 0
        while n < len(self.delayed):
            ret = self.process(copy.deepcopy(self.delayed[n]), False)
            if ret.get('delayed'):
                self.delayed[n] = copy.deepcopy(ret['delayed'])
            else:
                self.delayed.pop(n)

            if ret.get('next', False):
                return 'next'

            if ret.get('image_flow', False):
                n += 1

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
        while self.element_index <= len_elems:
            last = self.element_index == len_elems
            ret = self.process(self.elements[self.element_index], last=last)

            if ret.get('break', False):
                return 'break'

            self.element_index += 1
            if ret.get('delayed'):
                self.delayed.append(ret['delayed'])

            if ret.get('next', False):
                return 'next'

        return 'continue'

    def is_element_resetting(self):
        if self.will_reset or self.resetting:
            continue_reset = self.reset()
            return 'reset' if continue_reset else 'reset_done'
        else:
            return 'break'

    def process_add_ans(self, ans):
        if ans == 'break':
            return self.is_element_resetting()
        elif ans == 'next':
            should_continue = self.next_section()
            if not should_continue:
                return self.is_element_resetting()
            else:
                return 'reset'

    def run(self):
        while True:
            action = self.process_add_ans(self.add_delayed())
            if action == 'break':
                return False
            elif action == 'reset':
                continue
            elif action == 'reset_done':
                break

            action = self.process_add_ans(self.add_elements())
            if action == 'break':
                return False
            elif action == 'reset':
                continue
            elif action == 'reset_done':
                break

            if not self.resetting and self.cols_n > 1:
                if self.last_child_of_resetting():
                    break
                self.start_resetting()
                if self.will_reset:
                    self.reset()
                else:
                    return False
            else:
                self.minim_forward = False
                if not self.reset():
                    break

        if self.is_root and len(self.p.page):
            self.p.build_page()

        return True

    def last_child_of_resetting(self):
        parent = self.parent
        if parent:
            if self.last:
                if parent.resetting:
                    parent.mimim_forward = False
                    return True
                else:
                    return parent.last_child_of_resetting()
        return False


    def start_resetting(self):
        parent = self.parent
        if parent:
            if self.last and parent.cols_n > 1:
                parent.start_resetting()
                return

        self.will_reset = True

    def reset(self):
        if self.minim_diff_last and not self.minim_forward and (self.minim_diff_last - self.minim_diff) < 1:
            return False

        self.will_reset = False
        self.p.page = self.p.page[:self.page_index]
        self.go_to_beggining()
        self.starting = True

        if self.minim_diff is None:
            self.minim_diff = (self.max_y - self.min_y) / 2
            self.max_y = self.min_y + self.minim_diff
        else:
            self.minim_diff_last = self.minim_diff
            self.minim_diff /= 2
            if self.minim_forward:
                self.max_y += self.minim_diff
            else:
                self.max_y -= self.minim_diff

        self.resetting = True

        self.element_index = self.section_element_index
        self.delayed = copy.deepcopy(self.section_delayed)

        return True

    def go_to_beggining(self):
        self.y = self.min_y
        self.x = self.min_x
        self.column = 0

    def next_section(self, children_indexes=None):
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
                self.minim_forward = True
                return False
            elif self.is_root:
                self.p.build_page()
                self.p.pdf.add_page()
                self.go_to_beggining()
                self.starting = True
                self.section_element_index = self.element_index
                self.section_delayed = copy.deepcopy(self.delayed)
                if children_indexes is None:
                    return True
                else:
                    self.children_indexes = copy.deepcopy(children_indexes)
                    return {'min_x': self.min_x, 'min_y': self.min_y}
            else:
                self.section_element_index = self.element_index
                self.section_delayed = copy.deepcopy(self.delayed)
                if children_indexes is None:
                    new_children_indexes = [
                        { 'index': self.element_index, 'delayed': copy.deepcopy(self.delayed) }
                    ]
                else:
                    self.children_indexes = copy.deepcopy(children_indexes)
                    new_children_indexes = copy.deepcopy(children_indexes) + [self.element_index]

                ret = self.parent.next_section(new_children_indexes)
                if ret is False:
                    return False
                self.min_y = ret['min_y']
                self.min_x = ret['min_x']
                self.page_index = len(self.p.page)
                self.go_to_beggining()
                self.starting = True
                return True if children_indexes is None else ret
        else:
            self.column += 1
            self.starting = True
            self.y = self.min_y
            return True if children_indexes is None else \
                {'min_x': self.get_min_x(), 'min_y': self.min_y}

    def get_min_x(self):
        return self.min_x + self.column * (self.col_width + self.cols_gap)

    def move_y(self, h):
        self.height += h
        self.y += h

    def update_dimensions(self, style):
        s = style
        self.x = self.get_min_x() + s.get('margin_left', 0)
        self.width = self.col_width - s.get('margin_left', 0) - s.get('margin_right', 0)

        if self.starting:
            self.starting = False
        else:
            self.move_y(self.last_bottom + s.get('margin_top', 0))

        self.max_height = max(0, self.max_y - self.y)
        self.last_bottom = s.get('margin_bottom', 0)

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

        ret =  {'delayed': None, 'next': False}

        if isinstance(element, (str, list, tuple)): element = {'.': element}

        if not isinstance(element, dict):
            raise TypeError('Elements must be of type dict, str, list or tuple:'
                + str(element))

        style = {}
        style.update(self.style)
        # it was decided that the styles in content are always objects, not strings
        el_style = element.get('style', {})
        if isinstance(el_style, dict):
            style.update(el_style)

        self.update_dimensions(style)
        content = {'x': self.x, 'y': self.y}

        paragraph_keys = [key for key in element.keys() if key.startswith('.')]

        if len(paragraph_keys) > 0:
            par_style = {
                v: style.get(v) for v in self.paragraph_properties
                if style.get(v) is not None
            }
            key = paragraph_keys[0]
            pdf_text = self.p.pdf.create_text(
                {key: element[key], 'style': style.copy()},
                width = self.width, height = self.max_height, **par_style
            )
            content.update({'type': 'paragraph', 'content': pdf_text})
            self.p.page.append(content)

            self.move_y(pdf_text.current_height)
            if pdf_text.remaining is not None:
                ret = {'delayed': pdf_text.remaining, 'next': True}

        elif 'image' in element:
            pdf_image = self.p.pdf.create_image(element['image'])
            height = self.width * pdf_image.height/pdf_image.width

            if height < self.max_height:
                content.update({'type': 'image', 'width': self.width,
                    'height': height, 'content': pdf_image})
                self.p.page.append(content)
                self.move_y(height)
            else:
                image_place = style.get('image_place', 'flow')
                ret['delayed'] = element
                if image_place == 'normal':
                    ret['next'] = True
                elif image_place == 'flow':
                    ret['image_flow'] = True

        # elif 'r' in element:
        #     self.pdf.table()

        elif 'content' in element:
            pdf_content = PDFContentPart(
                element, self.p, self.get_min_x(), self.col_width, self.y,
                self.max_y, self, last, copy.deepcopy(style)
            )

            if (
                self.element_index == self.section_element_index
                and len(self.children_indexes)
            ):
                child = self.children_indexes[-1]
                if isinstance(child, int):
                    pdf_content.section_element_index = child
                    pdf_content.element_index = child
                    pdf_content.children_indexes = self.children_indexes[:-1]
                elif isinstance(child, dict):
                    pdf_content.section_element_index = child['index']
                    pdf_content.section_delayed = copy.deepcopy(child['delayed'])
                    pdf_content.element_index = child['index']
                    pdf_content.delayed = copy.deepcopy(child['delayed'])

            should_continue = pdf_content.run()
            if should_continue:
                if pdf_content.cols_n == 1:
                    self.move_y(pdf_content.y - pdf_content.min_y)
                else:
                    self.move_y(pdf_content.max_y - pdf_content.min_y)
            else:
                ret['break'] = True
        return ret