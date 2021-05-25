import copy

from .utils import process_style
from .text import PDFText
from .image import PDFImage


TABLE_PROPERTIES = ('widths', 'borders', 'fills')
PARAGRAPH_PROPERTIES = ('text_align', 'line_height', 'indent',
    'list_text', 'list_style', 'list_indent')

class PDFContent:
    def __init__(self, content, fonts, width, height, x=0, y=0, pdf=None):
        if not isinstance(content, dict):
            raise Exception('content must be a dict')

        self.content = content
        self.finished = False
        self.pdf_content_part = None
        self.setup(x, y, width, height)
        self.fonts = fonts
        self.current_height = 0
        self.pdf = pdf

    def setup(self, x=None, y=None, width=None, height=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.min_y = y
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

        self.max_y = self.min_y - self.height

    def run(self, x=None, y=None, width=None, height=None):
        self.setup(x, y, width, height)
        self.fills = []
        self.lines = []
        self.parts_ = []
        if self.pdf_content_part is None:
            self.pdf_content_part = PDFContentPart(self.content, self,
                self.x, self.width, self.min_y, self.max_y, last=True
            )
        ret = self.pdf_content_part.run()
        self.current_height = (
            self.pdf_content_part.y - self.pdf_content_part.min_y
            if self.pdf_content_part.cols_n == 1
            else self.pdf_content_part.max_y - self.pdf_content_part.min_y
        )
        if ret == 'finish':
            self.finished = True

class PDFContentPart:
    def __init__(
            self, content, pdf_content, min_x, width, min_y, max_y, parent=None,
            last=False, inherited_style=None
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
        self.style.update(process_style(content.get('style'), self.p.pdf))

        self.min_x = min_x
        self.min_y = min_y
        self.go_to_beggining()

        self.full_width = width
        self.max_y = max_y
        self.max_height = self.y - self.max_y
        self.last_bottom = 0

        column_info = content.get('cols', {'count': 1, 'gap': 10})

        if not isinstance(column_info, dict):
            raise TypeError('column_info must be a dict:'.format(column_info))

        self.cols_n = column_info.get('count', 1)
        self.cols_gap = column_info.get('gap', 10)
        cols_spaces = self.cols_gap * (self.cols_n - 1)
        self.col_width = (self.full_width - cols_spaces) / self.cols_n

        self.elements = content.get('content', [])

        self.section_element_index = 0  # index when the last section jump occured
        self.element_index = 0  # current index

        self.section_delayed = []  # delayed elements when the last section jump occured
        self.delayed = []  # current delayed elements

        self.children_indexes = []  # the last state of this element

        self.will_reset = False
        self.resetting = False
        self.parts_index = len(self.p.parts_)

        self.minim_diff_last = None
        self.minim_diff = None
        self.minim_forward = None

    def add_delayed(self):
        '''Function to add delayed elements to pdf.

        This function will try to add the delayed elements to the pdf, and it
        can return any of these strings:

        - 'continue' means caller could add all the delayed elements
        - 'break' means a parent element is reseting, and this instance must
          stop
        - 'next' means we need to move to the next section.
        '''
        n = 0
        while n < len(self.delayed):
            ret = self.process(copy.deepcopy(self.delayed[n]), False)
            if ret in ['break', 'finish']:
                return ret

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
        - 'break' means a parent element is reseting, and this instance must
          stop
        - 'next' means we need to move to the next section
        '''
        len_elems = len(self.elements) - 1
        while self.element_index <= len_elems:
            last = self.element_index == len_elems
            ret = self.process(self.elements[self.element_index], last=last)
            if ret in ['break', 'finish']:
                return ret

            self.element_index += 1
            if ret.get('delayed'):
                self.delayed.append(ret['delayed'])

            if ret.get('next', False):
                return 'next'

        return 'continue'

    def is_element_resetting(self):
        if self.will_reset or self.resetting:
            continue_reset = self.reset()
            return 'retry' if continue_reset else 'reset_done'
        else:
            return 'break'

    def process_add_ans(self, ans):
        if ans == 'finish':
            return 'finish'
        elif ans == 'break':
            return self.is_element_resetting()
        elif ans == 'next':
            next_section_ret = self.next_section()
            if next_section_ret == 'finish':
                return 'finish'
            elif next_section_ret == 'break':
                return self.is_element_resetting()
            else:
                return 'retry'

    def run(self):
        while True:
            action = self.process_add_ans(self.add_delayed())
            if action in ['break', 'finish']:
                return action
            elif action == 'retry':
                continue
            elif action == 'reset_done':
                break

            action = self.process_add_ans(self.add_elements())
            if action in ['break', 'finish']:
                return action
            elif action == 'retry':
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
                    return 'break'
            else:
                self.minim_forward = False
                if not self.reset():
                    break

        return 'continue'

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
        self.p.parts_ = self.p.parts_[:self.parts_index]
        self.go_to_beggining()

        if self.minim_diff is None:
            self.minim_diff = (self.min_y - self.max_y) / 2
            self.max_y += self.minim_diff
        else:
            self.minim_diff_last = self.minim_diff
            self.minim_diff /= 2
            if self.minim_forward:
                self.max_y -= self.minim_diff
            else:
                self.max_y += self.minim_diff

        self.resetting = True

        self.element_index = self.section_element_index
        self.delayed = copy.deepcopy(self.section_delayed)

        return True

    def go_to_beggining(self):
        self.y = self.min_y
        self.x = self.min_x
        self.column = 0
        self.starting = True

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

        if self.column == self.cols_n - 1:
            if self.is_root:
                self.section_element_index = self.element_index
                self.section_delayed = copy.deepcopy(self.delayed)
                if children_indexes is not None:
                    self.children_indexes = copy.deepcopy(children_indexes)
                return 'finish'
            elif self.resetting:
                self.minim_forward = True
                return 'break'
            else:
                self.section_element_index = self.element_index
                self.section_delayed = copy.deepcopy(self.delayed)
                if children_indexes is None:
                    new_children_indexes = [{
                        'index': self.element_index,
                        'delayed': copy.deepcopy(self.delayed)
                    }]
                else:
                    self.children_indexes = copy.deepcopy(children_indexes)
                    new_children_indexes = copy.deepcopy(children_indexes) \
                        + [self.element_index]

                ret = self.parent.next_section(new_children_indexes)
                if ret in ['break', 'finish']:
                    return ret
                self.min_y = ret['min_y']
                self.min_x = ret['min_x']
                self.parts_index = len(self.p.parts_)
                self.go_to_beggining()
                return 'continue' if children_indexes is None else ret
        else:
            self.column += 1
            self.starting = True
            self.y = self.min_y
            return 'continue' if children_indexes is None else \
                {'min_x': self.get_min_x(), 'min_y': self.min_y}

    def get_min_x(self):
        return self.min_x + self.column * (self.col_width + self.cols_gap)

    def update_dimensions(self, style):
        s = style
        self.x = self.get_min_x() + s.get('margin_left', 0)
        self.width = self.col_width - \
            s.get('margin_left', 0) - s.get('margin_right', 0)

        if self.starting:
            self.starting = False
        else:
            self.y -= self.last_bottom + s.get('margin_top', 0)

        self.max_height = max(0, self.y - self.max_y)
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

        ret = {'delayed': None, 'next': False}

        if not isinstance(element, (dict, str, list, tuple)):
            element = str(element)
        if isinstance(element, (str, list, tuple)):
            element = {'.': element}

        if not isinstance(element, dict):
            raise TypeError(
                'Elements must be of type dict, str, list or tuple:{}'
                .format(element)
            )

        style = {}
        style.update(self.style)
        element_style = process_style(element.get('style'), self.p.pdf)
        style.update(element_style)

        self.update_dimensions(style)

        paragraph_keys = [key for key in element.keys() if key.startswith('.')]

        if len(paragraph_keys) > 0 or 'paragraph' in element:
            if 'paragraph' in element:
                pdf_text = element['paragraph']
                pdf_text.setup(self.x, self.y, self.width, self.max_height)
                remaining = element
            else:
                par_style = {
                    v: style.get(v) for v in PARAGRAPH_PROPERTIES if v in style
                }
                key = paragraph_keys[0]
                pdf_text = PDFText(
                    {key: element[key], 'style': style.copy()},
                    self.width, self.max_height, self.x, self.y,
                    fonts=self.p.fonts, pdf=self.p.pdf, **par_style
                )
                remaining = {'paragraph': pdf_text, 'style': element_style}

            pdf_text.run()
            self.p.parts_.append({'type': 'paragraph', 'content': pdf_text})
            self.y -= pdf_text.current_height

            if not pdf_text.finished:
                ret = {'delayed': remaining, 'next': True}
        elif 'image' in element:
            pdf_image = PDFImage(
                element['image'], element.get('extension'),
                element.get('image_name')
            )
            height = self.width * pdf_image.height / pdf_image.width

            if height < self.max_height:
                self.p.parts_.append({
                    'type': 'image', 'x': self.x, 'y': self.y - height, 
                    'width': self.width, 'height': height, 'content': pdf_image
                })
                self.y -= height
            else:
                image_place = style.get('image_place', 'flow')
                ret['delayed'] = element
                if image_place == 'normal':
                    ret['next'] = True
                elif image_place == 'flow':
                    ret['image_flow'] = True

        elif 'table' in element or 'table_delayed' in element:
            if 'table_delayed' in element:
                pdf_table = element['table_delayed']
                pdf_table.setup(self.x, self.y, self.width, self.max_height)
                remaining = element
            else:
                table_props = {
                    v: element.get(v) for v in TABLE_PROPERTIES
                    if v in element
                }
                pdf_table = PDFTable(
                    element['table'], self.width, self.max_height, self.x,
                    self.y, style=style, pdf=self.p.pdf, **table_props
                )
                remaining = {'table_delayed': pdf_table, 'style': element_style}

            pdf_table.run()
            self.p.parts_.extend(pdf_table.parts_)
            self.p.lines.extend(pdf_table.lines)
            self.p.fills.extend(pdf_table.fills)

            self.y -= pdf_table.current_height

            if not pdf_table.finished:
                ret = {'delayed': remaining, 'next': True}

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
                    pdf_content.section_delayed = copy.deepcopy(
                        child['delayed']
                    )
                    pdf_content.element_index = child['index']
                    pdf_content.delayed = copy.deepcopy(child['delayed'])

            action = pdf_content.run()

            if action in ['finish', 'break']:
                return action
            else:
                if pdf_content.cols_n == 1:
                    self.y -= pdf_content.min_y - pdf_content.y
                else:
                    self.y -= pdf_content.min_y - pdf_content.max_y
                self.starting = False
        return ret

from .table import PDFTable