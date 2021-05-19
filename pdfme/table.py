from copy import deepcopy

from .color import PDFColor
from .text import PDFText
from .image import PDFImage
from .utils import process_style


PARAGRAPH_PROPERTIES = ('text_align', 'line_height', 'indent', 'list_text',
                        'list_style', 'list_indent')

TABLE_PROPERTIES = ('widths', 'borders', 'fills')


class PDFTable:
    def __init__(self, content, fonts, width, height, x=0, y=0, widths=None,
        style=None, borders=None, fills=None, pdf=None
    ):
        if not isinstance(content, (list, tuple)):
            raise Exception('content must be a list or tuple')

        self.setup(x, y, width, height)
        self.content = content
        self.current_row = 0
        self.fonts = fonts
        self.pdf = pdf
        self.finished = False
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
                raise Exception(
                    'at least one of the widths must be greater than zero')
        else:
            self.widths = [1 / cols_count] * cols_count

        self.style = {'cell_margin': 5, 'cell_fill': None}
        self.style.update(process_style(style, self.pdf))

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

    def decoration_first_step(self, obj):
        obj = deepcopy(obj)
        pos = obj.pop('p', None)
        if not pos:
            return None
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
            count = v_count if (vert and i == 0) or (
                not vert and i == 1) else h_count
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
            if ans is None:
                continue
            border, data, vert = ans
            border_l = self.borders_v if vert else self.borders_h
            self.decoration_second_step(self, data, vert, 
                h_count - 1 if vert else h_count,
                v_count if vert else v_count - 1
            )

            for i in data[0]:
                for j in data[i]:
                    border_l[i][j].update(border)
                    pdf_color = PDFColor(border_l[i][j]['color'], True)
                    border_l[i][j]['color'] = pdf_color

        self.fills_defs = {}

        for f in fills:
            ans = self.decoration_first_step(f)
            if ans is None:
                continue
            fill, data, vert = ans
            self.decoration_second_step(self, data, vert, h_count-1, v_count-1)
            for i in data[0]:
                for j in data[i]:
                    key = (j, i) if vert else (i, j)
                    self.fills_defs[key] = fill['color']

    def parse_style(self, style):
        cell_style = {}
        attr = 'cell_margin'
        for side in ('top', 'right', 'bottom', 'left'):
            cell_style[attr + '_' + side] = style.pop(attr + '_' + side,
                                                      style.get(attr, None))
        style.pop(attr, None)
        cell_style['cell_fill'] = style.pop('cell_fill', None)
        return cell_style

    def process_borders(self, col, border_left, border_top):
        vert_correction = border_top.get('width', 0)/2
        if not self.top_lines_interrupted:
            aux = self.top_lines[-1].get('width', 0)/2
            if aux > vert_correction:
                vert_correction = aux

        v_line = self.vert_lines[col]
        horiz_correction = border_left.get('width', 0)/2
        if not v_line['interrupted']:
            v_line['list'][-1]['y2'] = self.y_abs + vert_correction
            aux = v_line['list'][-1].get('width', 0)/2
            if aux > horiz_correction:
                horiz_correction = aux

        if not self.top_lines_interrupted:
            self.top_lines[-1]['x2'] = self.x_abs + horiz_correction

        if border_top['width'] > 0:   
            x2 = self.x_abs + self.widths[col] * self.width
            if (not self.top_lines_interrupted
                and self.top_lines[-1]['width'] == border_top['width']
                and self.top_lines[-1]['color'] == border_top['color']
                and self.top_lines[-1]['style'] == border_top['style']
            ):
                self.top_lines[-1]['x2'] = x2 + horiz_correction
            else:
                border_top.update(dict(type='line', y1=self.y_abs,
                    y2=self.y_abs, x2=x2, x1=self.x_abs - horiz_correction))
                self.top_lines.append(border_top)
                self.top_lines_interrupted = False
        else:
            self.top_lines_interrupted = True

        if border_left['width'] > 0:
            if not (not v_line['interrupted']
                and v_line['list'][-1]['width'] == border_left['width']
                and v_line['list'][-1]['color'] == border_left['color']
                and v_line['list'][-1]['style'] == border_left['style']
            ):
                border_left.update(dict(type='line', x1=self.x_abs,
                    x2=self.x_abs, y1=self.y_abs - vert_correction))
                v_line['list'].append(border_left)
                self.top_lines_interrupted = False
        else:
            v_line['interrupted'] = True

    def add_delayed(self):
        ret = self.add_row(self.delayed)
        return ret

    def run(self):
        self.parts_ = []
        self.lines = []
        self.fills = []
        col_count = len(self.content[0])
        self.rowspan = [None] * col_count
        self.vert_lines = [{'list': [], 'interrupted': True} 
            for i in range(col_count + 1)]
        self.current_height = 0

        can_continue = self.add_delayed()
        if not can_continue:
            return

        self.delayed = [None] * len(col_count)

        can_continue = True
        while self.current_row < len(self.content):
            can_continue = self.add_row(self.content[self.current_row])
            self.current_row += 1
            if not can_continue:
                break
        
        self.top_lines = []
        self.top_lines_interrupted = True
        self.y_abs = self.y + self.current_height
        for col in range(col_count):
            self.x_abs = self.x + self.widths[col] * self.width
            border_top = deepcopy(self.border_h[self.current_row][col])
            self.process_borders(col, {}, border_top)

        self.process_borders(col_count, {}, {})

        if can_continue:
            self.finished = True

    def add_row(self, row):
        self.max_height = 0
        self.accum_width = 0
        self.row_max_height = self.height - self.current_height
        self.colspan = 0
        self.top_lines = []
        self.top_lines_interrupted = True
        self.row_fills = []
        self.is_rowspan = False
        self.is_delayed = False
        self.y_abs = self.y + self.current_height
        for col, element in enumerate(row):
            self.x_abs = self.x + self.accum_width

            rowspan_memory = self.rowspan[col]
            border_left = deepcopy(self.border_v[col][self.current_row])
            border_top = deepcopy(self.border_h[self.current_row][col])
            should_continue = False
            if rowspan_memory is None:
                if self.colspan > 0:
                    self.colspan -= 1
                    border_left['width'] = 0
                    if self.is_rowspan:
                        border_top['width'] = 0
                        if self.colspan == 0:
                            self.is_rowspan = False
                    should_continue = True
            else:
                rowspan_memory['rows'] -= 1
                self.colspan = rowspan_memory['cols']
                self.is_rowspan = True
                border_top['width'] = 0

                if rowspan_memory['rows'] == 0:
                    self.rowspan[col] = None
                should_continue = True

            self.process_borders(col, border_left, border_top)
            if should_continue:
                continue

            if isinstance(element, dict) and 'delayed' in element:
                cell_style = element['cell_style']
            else:
                style = deepcopy(self.style)

                if element is None:
                    element = ''
                if not isinstance(element, (dict, str, list, tuple)):
                    element = str(element)
                if isinstance(element, (str, list, tuple)):
                    element = {'.': element}

                if not isinstance(element, dict):
                    raise TypeError(
                        'Elements must be of type dict, str, list or tuple:'
                        + str(element)
                    )

                style.update(process_style(element.get('style'), self.pdf))
                cell_style = self.parse_style(style)

            element = deepcopy(element)

            self.colspan = element.pop('colspan', 1) - 1
            rowspan = element.pop('rowspan', 1) - 1
            if rowspan > 0:
                self.rowspan[col] = {'rows': rowspan, 'cols': self.colspan}

            border_right = self.border_v[col + self.colspan + 1][self.current_row]
            border_bottom = self.border_h[self.current_row + rowspan + 1][col]

            full_width = sum(self.widths[col:col+self.colspan]) * self.width
            padd_x = border_left.get('width', 0)/2 + \
                cell_style['cell_margin_left']
            padd_y_top = border_top.get('width', 0)/2 + \
                cell_style['cell_margin_top']
            padd_y_bottom = border_bottom('width', 0)/2 + \
                cell_style['cell_margin_bottom']
            padd_y = padd_y_top + padd_y_bottom
            x = self.x_abs + padd_x
            y = self.y_abs + padd_y_top
            width = full_width - padd_x - border_right.get('width', 0) / 2 - \
                cell_style['cell_margin_right']
            height = self.row_max_height - padd_y_top - padd_y_bottom

            fill_color = cell_style.get('cell_fill', 
                self.fills_defs[(self.current_row, col)]
                if (self.current_row, col) in self.fills_defs
                else None
            )

            if fill_color is not None:
                self.row_fills.append({ 'type': 'fill', 'x': self.x_abs,
                    'y': self.y_abs, 'width': full_width,
                    'color': PDFColor(fill_color, stroke=False)
                })

            paragraph_keys = [
                key for key in element.keys() if key.startswith('.')]
            if len(paragraph_keys) > 0:
                par_style = {
                    v: style.get(v) for v in PARAGRAPH_PROPERTIES if v in style
                }
                key = paragraph_keys[0]
                pdf_text = PDFText(
                    {key: element[key], 'style': style}, self.fonts,
                    width=width, height=height, pdf=self.pdf, **par_style
                )
                pdf_text.run()

                real_height = pdf_text.current_height + padd_y

                if pdf_text.remaining is not None:
                    self.delayed[col] = pdf_text.remaining
                    self.is_delayed = True

                self.parts_.append({'x': x + self.accum_width, 'y': y,
                    'type': 'paragraph', 'content': pdf_text})

            elif 'image' in element:
                pdf_image = PDFImage(element['image'])
                img_width = width
                img_height = img_width * pdf_image.height/pdf_image.width

                image_added = True
                if img_height < height:
                    pass
                elif 'image_delayed' in element:
                    img_height = height
                    img_width = img_height * pdf_image.width / pdf_image.height
                else:
                    image_added = False
                    image_dict = deepcopy(element)
                    image_dict['image_delayed'] = True
                    self.delayed[col] = image_dict
                    self.is_delayed = True

                if image_added:
                    real_height = img_height + padd_y
                    self.parts_.append({'x': x + self.accum_width, 'y': y,
                        'type': 'image', 'width': img_width,
                        'height': img_height, 'content': pdf_image})

            elif ('content' in element or
                ('delayed' in element and element['type'] == 'content')
            ):
                if 'delayed' in element and element['type'] == 'content':
                    pdf_content = element['delayed']
                    pdf_content.setup(x, y, width, height)
                else:
                    element['style'] = style
                    pdf_content = PDFContent(
                        element, width, height, x, y, self.pdf
                    )

                pdf_content.run()

                self.parts_.extend(pdf_content.parts_)
                self.lines.extend(pdf_content.lines)
                self.fills.extend(pdf_content.fills)

                real_height = padd_y + pdf_content.current_height

                if not pdf_content.finished:
                    self.is_delayed = True
                    self.delayed[col] = {'delayed': pdf_content,
                        'type': 'content', 'cell_style': deepcopy(cell_style)}

            elif ('table' in element or
                ('delayed' in element and element['type'] == 'table')
            ):
                if 'delayed' in element and element['type'] == 'table':
                    pdf_table = element['delayed']
                    pdf_table.setup(x, y, width, height)
                else:
                    table_props = {v: element.get(v) for v in TABLE_PROPERTIES
                        if v in element}
                    pdf_table = PDFTable(
                        element['table'], width, height, x, y, style=style,
                        pdf=self.pdf, **table_props
                    )

                pdf_table.run()

                self.parts_.extend(pdf_table.parts_)
                self.lines.extend(pdf_table.lines)
                self.fills.extend(pdf_table.fills)

                real_height = pdf_table.current_height + padd_y

                if not pdf_table.finished:
                    self.is_delayed = True
                    self.delayed[col] = {'delayed': pdf_table,
                        'type': 'table', 'cell_style': deepcopy(cell_style)}

            self.accum_width += full_width
            if real_height > self.max_height:
                self.max_height = real_height

        last_border = self.border_v[len(row)][self.current_row]
        self.self.process_borders(len(row), last_border, {})

        for fill in self.row_fills:
            fill['height'] = self.max_height
            self.fills.append(fill)

        self.current_height += self.max_height

        return not self.is_delayed

from .content import PDFContent