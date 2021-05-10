from copy import deepcopy

from .color import PDFColor
from .utils import parse_margin
from .text import PDFText
from .image import PDFImage 


PARAGRAPH_PROPERTIES = ('text_align', 'line_height', 'indent', 'list_text',
    'list_style', 'list_indent')
class PDFTable:
    def __init__(self, content, width, height, x=0, y=0, widths=None,
        style=None, borders=None, fills=None
    ):
        if not isinstance(content, (list, tuple)):
            raise Exception('content must be a list or tuple')

        self.setup(x, y, width, height)
        self.content = content
        self.current_row = 0
        if len(content) == 0 or len(content[0]) == 0:
            return
        
        cols_count = len(content[0])
        self.delayed = [None] * cols_count
        self.borders_and_fills(borders, fills)

        if widths is not None:
            if not isinstance(widths, (list, tuple)):
                raise Exception('widths must be a list or tuple')
            if len(widths) != cols_count:
                raise Exception('widths count must be equal to cols count')
            try:
                widths_sum = sum(widths)
                self.widths = [w/widths_sum for w in widths]
            except TypeError:
                raise Exception('widths must be numbers')
            except ZeroDivisionError:
                raise Exception('at least one of the widths must be greater than zero')
        else:
            self.widths = [1 / cols_count] * cols_count

        self.style = {'cell_margin': 5, 'fill': None}

        if isinstance(style, dict):
            self.style.update(style)

        self.run()

    @property
    def parts(self):
        return self.fills + self.lines + self.parts_

    def setup(self, x=None, y=None, width=None, height=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        
    def decoration_first_step(self, obj_):
        obj = deepcopy(b)
        pos = obj.pop('p', None)
        if not pos: return None
        pos = pos.lower()
        data = pos.lower().split(';')
        data[0] = data[0][1:]
        if data[0] == '':
            data[0] = ':'
        if len(data) == 1:
            data.append(':')

        vert = pos.startswith('v')
        return obj, data, vert

    def decoration_second_step(self, data, vert, h_count, v_count):
        for i in range(2):
            count = v_count if (vert and i==0) or (not vert and i==1) else h_count
            if ':' in data[i]:
                parts = [int(j) for j in data[i].split(':')]
                parts[0] = 0 if parts[0].strip() == '' else int(parts[0])
                if len(parts) > 1:
                    num = count if parts[0].strip() == '' else int(parts[1])
                    parts[1] = num if num >= 0 else count + num
                if len(parts) > 2:
                    parts[2] = int(parts[2])
                data[i] = range(*parts)
            else:
                data[i] = (int(j) for j in data[i].split(','))

    def borders_and_fills(self, borders, fills):
        h_count = len(self.content) + 1
        v_count = len(self.content[0]) + 1
        self.borders_h = [[{'width': 1, 'color': 'black', 'style': 'solid'} 
            for j in range(v_count - 1)] for i in range(h_count)]
        self.borders_v = [[{'width': 1, 'color': 'black', 'style': 'solid'}
            for j in range(h_count - 1)] for i in range(v_count)]

        for b in borders:
            ans = self.decoration_first_step(b)
            if ans is None: continue
            border, data, vert = ans
            border_l = self.borders_v if pos.startswith('v') else self.borders_h
            self.decoration_second_step(self, data, vert,
                h_count - 1 if vert else h_count,
                v_count if vert else v_count - 1
            )
            
            for i in data[0]:
                for j in data[i]:
                    border_l[i][j].update(border)
        
        self.fills_defs = {}

        for f in fills:
            ans = self.decoration_first_step(f)
            if ans is None: continue
            fill, data, vert = ans
            self.decoration_second_step(self, data, vert, h_count-1, v_count-1)
            for i in data[0]:
                for j in data[i]:
                    key = (j, i) if vert else (i, j)
                    self.fills_defs[key] = fill

    def parse_style(self, style):
        cell_style = {}
        attr = 'cell_margin'
        for side in ('top', 'right', 'bottom', 'left'):
            cell_style[attr + '_' + side] = style.pop(attr + '_' + side,
                style.get(attr, None))
        style.pop(attr, None)
        return cell_style

    def add_delayed(self):

        self.delayed = [None] * len(self.content[0])

    def run(self):
        self.parts_ = []
        self.lines = []
        self.fills = []
        self.rowspan = [None] * len(self.content[0])
        for row in self.content[self.current_row:]:
            self.add_row(row)

    def add_row(self, row):
        max_height = 0
        accum_width = 0
        colspan = 0
        top_lines = []
        vert_lines = []
        is_rowspan = False
        for index, element in enumerate(row):
            rowspan_memory = self.rowspan[index]
            if rowspan_memory is None:
                if colspan > 0:
                    colspan -= 1
                    vert_lines.append(False)
                    if is_rowspan:
                        top_lines.append(False) 
                        if colspan == 0:
                            is_rowspan = False
                    else:
                        top_lines.append(True) 
                    continue
            else:
                rowspan_memory['rows'] -= 1
                colspan = rowspan_memory['cols']
                is_rowspan = True
                vert_lines.append(True)
                top_lines.append(False) 

                if rowspan_memory['rows'] == 0:
                    bottom_lines.append(rowspan_memory['bottom_line'])
                    self.rowspan[index] = None
                continue

            vert_lines.append(True)
            top_lines.append(True)

            style = deepcopy(self.style)

            if not isinstance(element, (dict, str, list, tuple)):
                element = str(element)
            if isinstance(element, (str, list, tuple)):
                element = {'.': element}

            if not isinstance(element, dict):
                raise TypeError('Elements must be of type dict, str, list or tuple:'
                    + str(element))

            el_style = element.get('style', {})
            if isinstance(el_style, dict):
                style.update(el_style)

            colspan = element.get('colspan', 1) - 1
            rowspan = element.get('rowspan', 1) - 1
            if rowspan > 0:
                self.rowspan[index] = {'rows': rowspan, 'cols': colspan}

            cell_style = self.parse_style(style)
            full_width = sum(self.widths[index:index+colspan]) * self.width
            padd_x = cell_style['border_width_left']/2 + cell_style['cell_margin_left']
            padd_y = cell_style['border_width_top']/2 + cell_style['cell_margin_top']
            x = self.x + accum_width + padd_x
            y = self.y + self.accum_height + padd_y
            width = full_width - padd_x - cell_style['border_width_right'] / 2 \
                - cell_style['cell_margin_right']
            height = self.height - self.accum_height - padd_y \
                - cell_style['border_width_bottom']/2 - cell_style['cell_margin_bottom']

            content = {'x': x + accum_width, 'y': y}

            paragraph_keys = [key for key in element.keys() if key.startswith('.')]
            if len(paragraph_keys) > 0:
                par_style = {
                    v: style.get(v) for v in PARAGRAPH_PROPERTIES if v in style
                }
                pdf_text = PDFText(
                    {key: element[paragraph_keys[0]], 'style': style.copy()},
                    width=width, height=height, **par_style
                )
                pdf_text.run()
                content.update({'type': 'paragraph', 'content': pdf_text})
                if pdf_text.remaining is not None:
                    self.delayed[index] = pdf_text.remaining
            elif 'image' in element:
                pdf_image = PDFImage(element['image'])
                height = self.width * pdf_image.height/pdf_image.width

                if height < self.max_height:
                    content.update({'type': 'image', 'width': self.width,
                        'height': height, 'content': pdf_image})
                    self.p.parts_.append(content)
                    self.move_y(height)
                else:
                    image_place = style.get('image_place', 'flow')
                    ret['delayed'] = element
                    if image_place == 'normal':
                        ret['next'] = True
                    elif image_place == 'flow':
                        ret['image_flow'] = True

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

                action = pdf_content.run()
                if action == 'break':
                    if pdf_content.cols_n == 1:
                        self.move_y(pdf_content.y - pdf_content.min_y)
                    else:
                        self.move_y(pdf_content.max_y - pdf_content.min_y)
                    self.starting = False
                else:
                    ret['break'] = True
            return ret

            
            
            
            self.parts_.append(content)





from .content import PDFContent