import copy
import re
from .color import pdf_color

class PDFText:
    def __init__(self, content, x, y, width, height, fonts):

        self.content = copy.deepcopy(content)
        self.x = x; self.y = y
        self.width = width
        self.height = height

        self.stream = ''
        self.line = []
        self.word = ''
        self.word_width = self.current_width = self.current_height = 0
        self.next_extra_height = self.extra_height = self.last_indent = 0
        
        self.max_size = 0
        self.text_align = self.content['style'].pop('text-align', 'l')
        self.line_height = self.content['style'].pop('line-height', 1.1)

        self.fonts = fonts

    def run(self):
        return self.process_content(self.content)

    def add_line(self):
        line_height = (self.max_size + self.extra_height) * self.line_height
        if self.current_height + line_height > self.height:
            return True

       # check_empty_line(self)
        line = ' {{:.3f}} -{:.3f} Td{}'.format(line_height, self.line)

        if self.text_align == 'j':
            pass
        elif self.text_align == 'l':
            self.stream += line.format(0)
        elif self.text_align == 'r':
            indent_ = self.width - self.current_width
            indent = indent_ - self.last_indent
            self.stream += line.format(indent)
            self.last_indent = indent_
        elif self.text_align == 'c':
            indent_ = (self.width - self.current_width)/2
            indent = indent_ - self.last_indent
            self.stream += line.format(indent)
            self.last_indent = indent_

        self.current_height += line_height

    def check_empty_line(self):
        last_chars = self.line[-2:]
        if last_chars[-2:-1] != ['\\'] and last_chars[-1:] == ['(']:
            self.line = self.line[:-1]
        else:
            self.line += ')Tj'

    def add_content(self, content, index):
        i = 0; j = 0
        self.line += '('
        space_width = self.get_char_size(' ')
        last_space = False
        n_content = len(content)
        while i <= n_content:
            last_word = i == n_content
            char = None if last_word else content[i]
            if last_word or char.isspace():
                if char == '\r':
                    pass
                elif self.current_width + space_width + self.word_width > self.width:
                    ret = self.add_line()
                    if ret:
                        return True

                    self.last_line_info = [index, content[j:]]
                    self.line_depth = 0

                    last_space = False if last_word or char == '\n' else True

                    if char == '\n':
                        pass

                    self.line = '(' + self.word
                    self.current_width = self.word_width
                    self.extra_height = self.next_extra_height
                    self.next_extra_height = 0
                    self.max_size = self.size

                    self.word = ''
                    self.word_width = 0
                    
                else:
                    if last_space:
                        self.line += ' '
                        # self.line_spaces += space_width
                        self.current_width += space_width

                    self.line += self.word
                    self.current_width += self.word_width
                    last_space = True
                    self.word = ''
                    self.word_width = 0
                    j = i
            else:
                self.word_width += self.get_char_size(char)
                if char in ['"', '(', ')']:
                    char = '\\' + char
                self.word += char

            i += 1

        #check_empty_line(self)

    def get_char_size(self, char):
        return self.size * self.fonts[self.font]['widths'][char] / 1000

    def process_content(self, element, root=True):
        # element = copy.deepcopy(element_)
        style = element.pop('style', {})
        if len(element) > 1 or len(element) == 0:
            raise ValueError('besides "style" key, content dicts must have only'
                ' one key of these c,b,i')
        elif 'b' in element and not 'font-weight' in style:
            style['font-weight'] = 'bold'
            contents = element['b']
        elif 'i' in element and not 'font-style' in style:
            style['font-style'] = 'oblique'
            contents = element['i']
        elif 'c' in element:
            contents = element['c']
        else:
            raise ValueError('besides "style" key, content dicts must have only'
                ' one key of these n,b,i')

        if any(e in style for e in ['font-size', 'font-family', 'font-weight', 'font-style']):
            f_weight = style.get('font-weight', 'normal')
            f_style = style.get('font-style', 'normal')
            if f_weight == 'bold' and f_style in ['italics', 'oblique']:
                self.font_style = 'bi'
            elif f_weight == 'bold':
                self.font_style = 'b'
            elif f_style in ['italics', 'oblique']:
                self.font_style = 'i'
            else:
                self.font_style = 'n'

            self.font_family, self.size = style['font-family'], style['font-size']

            font_name = self.fonts[self.font_family][self.font_style]['name']
            self.line.append('{} {} Tf'.format(font_name, self.size))

            if self.size > self.max_size:
                self.max_size = self.size

        if 'color' in style:
            self.line += ' ' + pdf_color(style['color'], False)
        if 'rise' in style:
            amount = self.size*style['rise']
            self.line += ' {} Ts'.format(amount)
            if amount < 0:
                self.next_extra_height = max(-amount, self.next_extra_height)
            elif amount + self.size > self.max_size:
                self.max_size = amount + self.size

        n_contents = len(contents)
        if not self.line_depth is None:
            self.line_depth += 1
        i = 0
        for i, content in enumerate(contents):
            if isinstance(content, str):
                ret = self.add_content(content, i)
            else:
                self.line += ' q'

                if not 'font-size' in content['style']: content['style']['font-size'] = style['font-size']
                if not 'font-family' in content['style']: content['style']['font-family'] = style['font-family']
                if not 'font-weight' in content['style']: content['style']['font-weight'] = style['font-weight'] 
                if not 'font-style' in content['style']: content['style']['font-style'] = style['font-style']

                ret = self.process_content(content, False)
                self.font, self.size = style['font-family'], style['font-size']
                self.line += ' Q'

            if ret is None:
                pass
            elif isinstance(ret, bool) and ret:
                if self.line_depth > 0:
                    self.line_depth -= 1
                    self.stream += ' Q'
                    return True
                else:
                    index, text = self.last_line_info
                    ret = {'content': [text], 'style': style}
                    if index + 1 < n_contents:
                        ret['content'] += contents[index + 1:]
                    return ret
            else:
                ret = {'content': [ret], 'style': style}
                if i + 1 < n_contents:
                    ret['content'] += contents[i + 1:]
                return ret

        if root and len(self.line) > 0:
            self.line += '('
            ret = self.add_line()
            if ret:
                return {'content': [self.last_line_info[1]], 'style': style}

        else:
            if not self.line_depth is None:
                self.line_depth -= 1
