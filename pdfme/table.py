from copy import deepcopy

from .color import PDFColor
from .utils import parse_margin

class PDFTable:
    def __init__(self, content, width, height, widths=None, style=None):

        if not isinstance(content, (list, tuple)):
            raise Exception('content must be a list or tuple')

        self.cells = []
        self.h_lines = {}
        self.v_lines = {}
        self.fills = []
        self.delayed = None
        self.width = width
        self.height = height
        self.content = content
        if len(content) == 0 or len(content[0]) == 0:
            return
        
        cols_count = len(content[0])
        self.delayed = [None] * cols_count

        if widths is not None:
            if not isinstance(widths, (list, tuple)):
                raise Exception('widths must be a list or tuple')
            if len(widths) != cols_count:
                raise Exception('widths count must be equal to cols count')
            try:
                widths_sum = sum(widths)
                self.widths = [self.width * w/widths_sum for w in widths]
            except TypeError:
                raise Exception('widths must be numbers')
            except ZeroDivisionError:
                raise Exception('at least one of the widths must be greater than zero')
        else:
            col_width = self.width / cols_count
            self.widths = [col_width] * cols_count

        default_border_style = {'width': 1, 'color': 'black'}

        self.style = style if isinstance(style, dict) else {
            'border_width': 1,
            'border_color': 'black',
            'margin': 5,
            'fill': None
        }
        
        self.run()

    def parse_style(self, style):
        for attr in ('border_color', 'border_color', 'margin'):
            if attr in style:
                for side in ('top', 'right', 'bottom', 'left'):
                    if attr + '_' + side not in style:
                        style[attr + '_' + side] = style[attr]

    def run(self):
        y = 0
        for row in self.content:
            i = 0
            for i, cell in enumerate(row):
                style = deepcopy(self.style)
                if isinstance(cell, dict):
                    style.update(cell.get('style'), {})
                    self.parse_style(style)
                
                    colspan = cell.get('colspan', 1) - 1
                    rowspan = cell.get('rowspan', 1) - 1

                    width = sum(self.widths[i:i+colspan])
                    