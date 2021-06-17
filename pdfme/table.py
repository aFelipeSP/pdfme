from copy import deepcopy

from .color import PDFColor
from .text import PDFText
from .image import PDFImage
from .utils import process_style


PARAGRAPH_PROPS = (
    'text_align', 'line_height', 'indent', 'list_text',
    'list_style', 'list_indent'
)

TABLE_PROPS = ('widths', 'borders', 'fills')

class PDFTable:
    def __init__(
        self, content, fonts, width, height, x=0, y=0, widths=None,
        style=None, borders=None, fills=None, pdf=None
    ):
        if not isinstance(content, (list, tuple)):
            raise Exception('content must be a list or tuple')

        self.setup(x, y, width, height)
        self.content = content
        self.current_index = 0
        self.fonts = fonts
        self.pdf = pdf
        self.finished = False
        if len(content) == 0 or len(content[0]) == 0:
            return

        self.cols_count = len(content[0])
        self.delayed = {}

        if widths is not None:
            if not isinstance(widths, (list, tuple)):
                raise Exception('widths must be a list or tuple')
            if len(widths) != self.cols_count:
                raise Exception('widths count must be equal to cols count')
            try:
                widths_sum = sum(widths)
                self.widths = [w/widths_sum for w in widths]
            except TypeError:
                raise Exception('widths must be numbers')
            except ZeroDivisionError:
                raise Exception('sum of widths must be greater than zero')
        else:
            self.widths = [1 / self.cols_count] * self.cols_count

        self.style = {'cell_margin': 5, 'cell_fill': None}
        self.style.update(process_style(style, self.pdf))
        self.set_default_border()
        self.setup_borders([] if borders is None else borders)
        self.setup_fills([] if fills is None else fills)

    def setup(self, x=None, y=None, width=None, height=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

    def set_default_border(self):
        self.default_border = {}
        self.default_border['width'] = self.style.pop('border_width', 1)
        color = self.style.pop('border_color', 0)
        self.default_border['color'] = PDFColor(color, True)
        self.default_border['style'] = self.style.pop('border_style', 'solid')

    def parse_style_string(self, pos, counts):
        range_strs = pos.split(';')
        if len(range_strs) == 1:
            range_strs.append(':')
        ranges = [
            self.parse_range_string(range_str, count)
            for range_str, count in zip(range_strs, counts)
        ]
        for i in ranges[0]:
            for j in ranges[1]:
                yield i, j

    def range_generator(self, list_str, count):
        for i in list_str.split(','):
            num = int(i)
            yield num if num >= 0 else count + num

    def parse_range_string(self, data, count):
        data = ':' if data == '' else data
        if ':' in data:
            parts = data.split(':')
            num = 0 if parts[0].strip() == '' else int(parts[0])
            parts[0] = num if num >= 0 else count + num
            if len(parts) > 1:
                num = count if parts[1].strip() == '' else int(parts[1])
                parts[1] = num if num >= 0 else count + num
            if len(parts) > 2:
                parts[2] = 1 if parts[2].strip() == '' else int(parts[2])
            return range(*parts)
        else:
            return [i for i in self.range_generator(data, count)]

    def setup_borders(self, borders):
        rows = len(self.content)
        cols = self.cols_count
        self.borders_h = {}
        self.borders_v = {}
        for b in borders:
            border = deepcopy(deepcopy(self.default_border))
            border.update(b)
            border['color'] = PDFColor(border['color'], True)
            pos = border.pop('pos', None)
            if pos is None:
                continue
            is_vert = pos[0].lower() == 'v'
            counts = (rows, cols + 1) if is_vert else (rows + 1, cols)
            border_l = self.borders_v if is_vert else self.borders_h
            for i, j in self.parse_style_string(pos[1:], counts):
                first = border_l.setdefault(i, {})
                first[j] = border

    def get_border(self, i, j, is_vert):
        border_l = self.borders_v if is_vert else self.borders_h
        if i in border_l and j in border_l[i]:
            return deepcopy(border_l[i][j])
        else:
            return deepcopy(self.default_border)

    def setup_fills(self,  fills):
        v_count = len(self.content)
        h_count = self.cols_count
        self.fills_defs = {}
        for f in fills:
            fill = f['color']
            pos = f.get('pos', None)
            if pos is None:
                continue
            for i, j in self.parse_style_string(pos, (v_count, h_count)):
                first = self.fills_defs.setdefault(i, {})
                first[j] = fill

    def get_cell_style(self, style):
        cell_style = {}
        attr = 'cell_margin'
        for side in ('top', 'right', 'bottom', 'left'):
            cell_style[attr + '_' + side] = style.pop(
                attr + '_' + side, style.get(attr, None)
            )
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
            v_line['list'][-1]['y2'] = self.y_abs - vert_correction
            aux = v_line['list'][-1].get('width', 0)/2
            if aux > horiz_correction:
                horiz_correction = aux

        if not self.top_lines_interrupted:
            self.top_lines[-1]['x2'] += horiz_correction

        if border_top.get('width', 0) > 0:
            x2 = self.x_abs + self.widths[col] * self.width
            if (not self.top_lines_interrupted
                and self.top_lines[-1]['width'] == border_top['width']
                and self.top_lines[-1]['color'] == border_top['color']
                and self.top_lines[-1]['style'] == border_top['style']
            ):
                self.top_lines[-1]['x2'] = x2
            else:
                border_top.update(dict(
                    type='line', y1=self.y_abs,
                    y2=self.y_abs, x2=x2, x1=self.x_abs - horiz_correction
                ))
                self.top_lines.append(border_top)
                self.top_lines_interrupted = False
        else:
            self.top_lines_interrupted = True

        if border_left.get('width', 0) > 0:
            if not (
                not v_line['interrupted']
                and v_line['list'][-1]['width'] == border_left['width']
                and v_line['list'][-1]['color'] == border_left['color']
                and v_line['list'][-1]['style'] == border_left['style']
            ):
                border_left.update(dict(
                    type='line', x1=self.x_abs,
                    x2=self.x_abs, y1=self.y_abs + vert_correction
                ))
                v_line['list'].append(border_left)
                v_line['interrupted'] = False
        else:
            v_line['interrupted'] = True

    def get_delayed_cols_n(self):
        return sum(v['colspan'] for v in self.delayed.values())

    def can_continue(self):
        if self.get_delayed_cols_n() == self.cols_count:
            return False
        for col in self.delayed:
            if not col in self.rowspan:
                return False
        return True

    def get_cell_dimensions(
        self, col, border_left, border_top, cell_style, rowspan, colspan
    ):
        border_right = self.get_border(
            self.current_index, col + colspan + 1, True
        )
        border_bottom = self.get_border(
            self.current_index + rowspan + 1, col, False
        )

        full_width = sum(self.widths[col:col + colspan + 1]) * self.width
        padd_x_left = border_left.get('width', 0) / 2 + \
            cell_style['cell_margin_left']
        padd_x_right = border_right.get('width', 0) / 2 + \
            cell_style['cell_margin_right']
        padd_x = padd_x_left + padd_x_right
        padd_y_top = border_top.get('width', 0) / 2 + \
            cell_style['cell_margin_top']
        padd_y_bottom = border_bottom.get('width', 0) / 2 + \
            cell_style['cell_margin_bottom']
        padd_y = padd_y_top + padd_y_bottom
        x = self.x_abs + padd_x_left
        y = self.y_abs - padd_y_top
        width = full_width - padd_x
        height = self.row_max_height - padd_y
        return x, y, width, height, padd_x, padd_y

    def run(self, x=None, y=None, width=None, height=None):
        self.setup(x, y, width, height)
        self.parts_ = []
        self.lines = []
        self.fills = []
        self.fills_mem = {}
        self.heights_mem = {}
        self.rowspan = {}
        self.vert_lines = [
            {'list': [], 'interrupted': True}
            for i in range(self.cols_count + 1)
        ]
        self.current_height = 0

        can_continue = True
        if len(self.delayed) > 0:
            can_continue = self.add_row([self.delayed.get(i) for i in range(self.cols_count)], True)
            if can_continue:
                self.current_index += 1
        if can_continue:
            while self.current_index < len(self.content):
                can_continue = self.add_row(self.content[self.current_index])
                if can_continue:
                    self.current_index += 1
                else:
                    break

        self.top_lines = []
        self.top_lines_interrupted = True
        self.y_abs = self.y - self.current_height
        for col in range(self.cols_count):
            self.x_abs = self.x + sum(self.widths[0:col]) * self.width
            border_top = self.get_border(self.current_index, col, False)
            self.process_borders(col, {}, border_top)

        self.x_abs = self.x + self.width
        self.process_borders(self.cols_count, {}, {})
        self.lines.extend(self.top_lines)
        self.lines.extend(line for vert_line in self.vert_lines for line in vert_line['list'])

        if self.current_index >= len(self.content) and len(self.delayed) == 0:
            self.finished = True

    def add_row(self, row, is_delayed=False):
        self.max_height = 0
        self.row_max_height = self.height - self.current_height
        self.colspan = 0
        self.top_lines = []
        self.top_lines_interrupted = True
        self.is_rowspan = False
        self.y_abs = self.y - self.current_height
        for col, element in enumerate(row):
            self.x_abs = self.x + sum(self.widths[0:col]) * self.width
            rowspan_memory = self.rowspan.get(col, None)
            border_left = self.get_border(self.current_index, col, True)
            border_top = self.get_border(self.current_index, col, False)
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
            elif not is_delayed:
                rowspan_memory['rows'] -= 1
                self.colspan = rowspan_memory['cols']
                self.is_rowspan = True
                border_top['width'] = 0

                if rowspan_memory['rows'] == 0:
                    self.rowspan.pop(col)
                    if col in self.fills_mem:
                        self.fills_mem[col]['add_later'] = False
                    if self.heights_mem.get(col, 0) > self.max_height:
                        self.max_height = self.heights_mem[col]
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
                cell_style = self.get_cell_style(style)

            element = deepcopy(element)

            colspan_original = element.get('colspan', 1)
            self.colspan = colspan_original - 1
            row_added = element.get('row', self.current_index)
            rowspan = element.get('rowspan', 1) - 1 - self.current_index + \
                row_added
            if rowspan > 0:
                self.rowspan[col] = {'rows': rowspan, 'cols': self.colspan}

            x, y, width, height, padd_x, padd_y = self.get_cell_dimensions(
                col, border_left, border_top, cell_style, rowspan, self.colspan
            )

            real_height = 0

            delayed = {
                'cell_style': cell_style, 'colspan': colspan_original,
                'rowspan': element.get('rowspan', 1), 'row': row_added
            }

            fill_color = cell_style.get('cell_fill',
                self.fills_defs[(self.current_index, col)]
                if (self.current_index, col) in self.fills_defs
                else None
            )

            if fill_color is not None:
                self.fills_mem[col] = { 'type': 'fill', 'x': self.x_abs,
                    'y': self.y_abs, 'width': width + padd_x, 'height': 0,
                    'color': PDFColor(fill_color, stroke=False)
                }
                if rowspan > 0:
                    self.fills_mem[col]['add_later'] = True

            keys = [key for key in element.keys() if key.startswith('.')]
            if (
                len(keys) > 0 or
                ('delayed' in element and element['type'] == 'text')
            ):
                if 'delayed' in element:
                    pdf_text = element['delayed']
                    pdf_text.setup(x, y, width, height)
                else:
                    par_style = {
                        v: style.get(v) for v in PARAGRAPH_PROPS if v in style
                    }
                    key = keys[0]
                    pdf_text = PDFText(
                        {key: element[key], 'style': style},
                        width, height, x, y,
                        fonts=self.fonts, pdf=self.pdf, **par_style
                    )

                result = pdf_text.run()
                result['type'] = 'paragraph'
                self.parts_.append(result)
                real_height = pdf_text.current_height + padd_y

                if not pdf_text.finished:
                    delayed.update({'delayed': pdf_text, 'type': 'text'})
                    self.delayed[col] = delayed
                else:
                    self.delayed.pop(col, None)
            elif (
                'image' in element or
                ('delayed' in element and element['type'] == 'image')
            ):
                if 'delayed' in element:
                    pdf_image = element['delayed']
                else:
                    pdf_image = PDFImage(element['image'])
                img_width = width
                img_height = img_width * pdf_image.height / pdf_image.width

                if img_height < height:
                    real_height = img_height + padd_y
                    self.parts_.append({
                        'type': 'image', 'pdf_image': pdf_image,
                        'x': x, 'y': y - img_height,
                        'width': img_width, 'height': img_height
                    })
                    self.delayed.pop(col, None)
                else:
                    delayed.update({'delayed': pdf_image, 'type': 'image'})
                    self.delayed[col] = delayed
            elif (
                'content' in element or
                ('delayed' in element and element['type'] == 'content')
            ):
                if 'delayed' in element and element['type'] == 'content':
                    pdf_content = element['delayed']
                    pdf_content.setup(x, y, width, height)
                else:
                    element['style'] = style
                    pdf_content = PDFContent(
                        element, self.fonts, width, height, x, y, self.pdf
                    )

                pdf_content.run()

                self.parts_.extend(pdf_content.parts_)
                self.lines.extend(pdf_content.lines)
                self.fills.extend(pdf_content.fills)

                real_height = padd_y + pdf_content.current_height

                if not pdf_content.finished:
                    delayed.update({'delayed': pdf_content, 'type': 'content'})
                    self.delayed[col] = delayed
                else:
                    self.delayed.pop(col, None)

            elif (
                'table' in element or
                ('delayed' in element and element['type'] == 'table')
            ):
                if 'delayed' in element and element['type'] == 'table':
                    pdf_table = element['delayed']
                    pdf_table.setup(x, y, width, height)
                else:
                    table_props = {
                        v: element.get(v) for v in TABLE_PROPS if v in element
                    }
                    pdf_table = PDFTable(
                        element['table'], self.fonts, width, height, x, y,
                        style=style, pdf=self.pdf, **table_props
                    )

                pdf_table.run()

                self.parts_.extend(pdf_table.parts_)
                self.lines.extend(pdf_table.lines)
                self.fills.extend(pdf_table.fills)

                real_height = pdf_table.current_height + padd_y

                if not pdf_table.finished:
                    delayed.update({'delayed': pdf_table, 'type': 'table'})
                    self.delayed[col] = delayed
                else:
                    self.delayed.pop(col, None)

            if rowspan > 0:
                self.heights_mem[col] = real_height
                real_height = 0

            if real_height > self.max_height:
                self.max_height = real_height

        ret = self.can_continue()

        self.x_abs = self.x + self.width
        last_border = self.get_border(self.current_index, len(row), True)
        self.process_borders(len(row), last_border, {})

        self.lines.extend(self.top_lines)

        for col in self.heights_mem:
            self.heights_mem[col] -= self.max_height

        for col, fill in list(self.fills_mem.items()):
            fill['height'] += self.max_height
            if not fill.get('add_later', False) or not ret:
                fill['y'] -= fill['height']
                self.fills.append(fill)
                self.fills_mem.pop(col)

        self.current_height += self.max_height

        return ret

from .content import PDFContent
