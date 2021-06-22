import copy

from .utils import parse_style_str, process_style
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
        content_part = self.pdf_content_part
        if content_part is None:
            self.pdf_content_part = content_part = PDFContentPart(
                self.content, self, self.x, self.width, self.min_y, self.max_y,
                last=True
            )
        else:
            content_part.init(self.x, self.width, self.min_y, self.max_y)

        ret = content_part.run()
        self.current_height = content_part.min_y - (
            content_part.max_y if content_part.cols_n > 1 else content_part.y
        )
        if ret == 'continue':
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

        self.column_info = content.get('cols', {'count': 1, 'gap': 10})

        if not isinstance(self.column_info, dict):
            raise TypeError(
                'self.column_info must be a dict:'.format(self.column_info)
            )
        self.elements = content.get('content', [])

        self.section_element_index = 0  # index when the last section jump occured
        self.section_delayed = []  # delayed elements when the last section jump occured
        self.children_indexes = []  # the last state of this element
        self.other_children_indexes = None

        self.init(min_x, width, min_y, max_y)

    def init(self, min_x, width, min_y, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.go_to_beginning()

        self.full_width = width
        self.max_y = max_y
        self.max_height = self.y - self.max_y
        self.last_bottom = 0

        self.cols_n = self.column_info.get('count', 1)
        self.cols_gap = self.column_info.get('gap', max(width / 25, 7))
        cols_spaces = self.cols_gap * (self.cols_n - 1)
        self.col_width = (width - cols_spaces) / self.cols_n

        self.element_index = self.section_element_index # current index
        self.delayed = copy.deepcopy(self.section_delayed) # current delayed elements
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
            if ret in ['interrupt', 'break', 'partial_next']:
                return ret

            if ret.get('delayed'):
                self.delayed[n] = copy.deepcopy(ret['delayed'])
            else:
                self.delayed.pop(n)

            if ret.get('next', False):
                return 'next'

            if ret.get('image_flow', False):
                n += 1

        if (
            len(self.delayed) > 0 and
            self.element_index >= len(self.elements) - 1
        ):
            return 'next'

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
            if ret in ['interrupt', 'break', 'partial_next']:
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
            return 'retry' if continue_reset else 'continue'
        else:
            return 'break'

    def process_add_ans(self, ans):
        if ans == 'interrupt':
            return ans
        elif ans == 'partial_next':
            if self.other_children_indexes is None:
                return ans
            else:
                return 'retry'
        elif ans == 'break':
            return self.is_element_resetting()
        elif ans == 'next':
            next_section_ret = self.next_section()
            if next_section_ret == 'break':
                return self.is_element_resetting()
            else:
                return next_section_ret

    def run(self):
        while True:
            action = self.process_add_ans(self.add_delayed())
            if action == 'retry':
                continue
            elif action in ['interrupt', 'break', 'partial_next']:
                return action

            action = self.process_add_ans(self.add_elements())
            if action == 'retry':
                continue
            elif action in ['interrupt', 'break', 'partial_next']:
                return action

            if len(self.delayed) > 0:
                continue

            if not self.resetting and self.cols_n > 1:
                if self.last_child_of_resetting():
                    break
                self.start_resetting()
                if self.will_reset:
                    self.reset()
                else:
                    return 'break'
            elif self.resetting:
                self.minim_forward = False
                if not self.reset():
                    break
            else:
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
                # elif len(parent.delayed) == 0:
                    return parent.last_child_of_resetting()
        return False

    def start_resetting(self):
        parent = self.parent
        if parent and self.last  and parent.cols_n > 1:
            # and len(parent.delayed) == 0
            parent.start_resetting()
            return

        self.will_reset = True

    def reset(self):
        if self.minim_diff_last and self.minim_diff_last - self.minim_diff < 1:
            if self.minim_forward:
                self.minim_diff *= 2
            else:
                return False

        self.will_reset = False
        self.p.parts_ = self.p.parts_[:self.parts_index]
        self.go_to_beginning()

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

    def go_to_beginning(self):
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
            if self.resetting:
                self.minim_forward = True
                return 'break'
            else:
                self.section_element_index = self.element_index
                self.section_delayed = copy.deepcopy(self.delayed)
                new_index = {
                    'index': self.element_index,
                    'delayed': copy.deepcopy(self.delayed)
                }
                if children_indexes is None:
                    self.children_indexes = []
                    new_children_indexes = [new_index]
                else:
                    self.children_indexes = copy.deepcopy(children_indexes)
                    new_children_indexes = copy.deepcopy(children_indexes)
                    new_children_indexes.append(new_index)

                if self.is_root:
                    return 'interrupt'

                ret = self.parent.next_section(new_children_indexes)
                if ret in ['interrupt', 'break', 'partial_next']:
                    return ret
                self.min_y = ret['min_y']
                self.min_x = ret['min_x']
                self.parts_index = len(self.p.parts_)
                self.go_to_beginning()
                return 'retry' if children_indexes is None else ret
        else:
            self.column += 1
            self.starting = True
            self.y = self.min_y

            if len(self.delayed) > 0 and children_indexes is not None:
                self.other_children_indexes = copy.deepcopy(children_indexes)
                return 'partial_next'

            return 'retry' if children_indexes is None else \
                {'min_x': self.get_min_x(), 'min_y': self.min_y}

    def get_min_x(self):
        return self.min_x + self.column * (self.col_width + self.cols_gap)

    def update_dimensions(self, style):
        s = style
        self.x = self.get_min_x() + s.get('margin_left', 0)
        self.width = self.col_width - \
            s.get('margin_left', 0) - s.get('margin_right', 0)

        if not self.starting:
            self.y -= self.last_bottom

        self.max_height = max(0, self.y - self.max_y)
        self.last_bottom = s.get('margin_bottom', 0)

    def add_top_margin(self, style):
        if self.starting:
            self.starting = False
        else:
            self.y -=  style.get('margin_top', 0)

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
        if not isinstance(element, (dict, str, list, tuple)):
            element = str(element)
        if isinstance(element, (str, list, tuple)):
            element = {'.': element}

        if not isinstance(element, dict):
            raise TypeError(
                'Elements must be of type dict, str, list or tuple:{}'
                .format(element)
            )

        keys = [key for key in element.keys() if key.startswith('.')]

        style = {}
        style.update(self.style)
        if len(keys) > 0:
            style.update(parse_style_str(keys[0][1:], self.p.fonts))
        element_style = process_style(element.get('style'), self.p.pdf)
        style.update(element_style)

        self.update_dimensions(style)

        if len(keys) > 0 or 'paragraph' in element:
            return self.process_text(element, style, element_style, keys)
        elif 'image' in element:
            return self.process_image(element, style)
        elif 'table' in element or 'table_delayed' in element:
            return self.process_table(element, style, element_style)
        elif 'content' in element:
            return self.process_child(element, style, last)

    def process_text(self, element, style, element_style, paragraph_keys):
        if 'paragraph' in element:
            pdf_text = element['paragraph']
            pdf_text.setup(
                self.x, self.y, self.width, self.max_height,
                element['last_part'], element['last_word']
            )
            pdf_text.pdf = self.p.pdf
            remaining = copy.deepcopy(element)
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

        result = pdf_text.run()
        remaining['last_part'] = pdf_text.last_part
        remaining['last_word'] = pdf_text.last_word
        result['type'] = 'paragraph'
        self.p.parts_.append(result)
        self.y -= pdf_text.current_height

        if pdf_text.current_height > 0:
            self.add_top_margin(style)

        if pdf_text.finished:
            return {'delayed': None, 'next': False}
        else:
            return {'delayed': remaining, 'next': True}

    def process_image(self, element, style):
        ret = {'delayed': None, 'next': False}
        pdf_image = PDFImage(
            element['image'], element.get('extension'),
            element.get('image_name')
        )
        height = self.width * pdf_image.height / pdf_image.width

        if height < self.max_height:
            self.p.parts_.append({
                'pdf_image': pdf_image, 'type': 'image', 'x': self.x,
                'y': self.y - height, 'width': self.width, 'height': height
            })
            self.y -= height
            self.add_top_margin(style)
        else:
            image_place = style.get('image_place', 'flow')
            ret['delayed'] = element
            if image_place == 'normal':
                ret['next'] = True
            elif image_place == 'flow':
                ret['image_flow'] = True
        return ret

    def process_table(self, element, style, element_style):
        if 'table_delayed' in element:
            pdf_table = element['table_delayed']
            pdf_table.setup(self.x, self.y, self.width, self.max_height)
            pdf_table.pdf = self.p.pdf
            remaining = element
        else:
            table_props = {
                v: element.get(v) for v in TABLE_PROPERTIES
                if v in element
            }
            pdf_table = PDFTable(
                element['table'], self.p.fonts, self.width, self.max_height,
                self.x, self.y, style=style, pdf=self.p.pdf, **table_props
            )
            remaining = {'table_delayed': pdf_table, 'style': element_style}

        pdf_table.run()
        self.p.parts_.extend(pdf_table.parts_)
        self.p.lines.extend(pdf_table.lines)
        self.p.fills.extend(pdf_table.fills)

        self.y -= pdf_table.current_height
        if pdf_table.current_height > 0:
            self.add_top_margin(style)

        if not pdf_table.finished:
            return {'delayed': remaining, 'next': True}
        else:
            return {'delayed': None, 'next': False}

    def process_child(self, element, style, last):
        pdf_content = PDFContentPart(
            element, self.p, self.get_min_x(), self.col_width, self.y,
            self.max_y, self, last, copy.deepcopy(style)
        )
        down_condition1 = len(self.children_indexes) > 0 and \
            self.element_index == self.section_element_index
        down_condition2 = self.other_children_indexes is not None

        if down_condition1 or down_condition2:
            child = self.children_indexes[-1] if down_condition1 else \
                self.other_children_indexes[-1]
            pdf_content.section_element_index = child['index']
            pdf_content.section_delayed = copy.deepcopy(child['delayed'])
            pdf_content.element_index = child['index']
            pdf_content.delayed = copy.deepcopy(child['delayed'])
            pdf_content.children_indexes = self.children_indexes[:-1] \
                if down_condition1 else self.other_children_indexes[:-1]

            self.other_children_indexes = None

        action = pdf_content.run()

        current_height = pdf_content.min_y - (
            pdf_content.max_y if pdf_content.cols_n > 1 else pdf_content.y
        )
        self.y -= current_height

        if current_height > 0:
            self.add_top_margin(style)

        if action in ['interrupt', 'break', 'partial_next']:
            return action
        else:
            self.starting = False
            return {'delayed': None, 'next': False}

from .table import PDFTable
