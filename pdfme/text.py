import copy
import re
from .color import pdf_color

ELEMENT_ERROR = ("Text elements must be strings or dicts, and if they are dicts "
    "they must have one of these keys (with more text elements nested on it) "
    "['n','b','i'], and optionally a 'style' key. Element: {}")
class PDFText:
    def __init__(self, content, fonts, 
        width = 200,
        height = 200,
        font_family='Helvetica',
        font_size=11,
        font_weight = 'normal',
        font_style = 'normal',
        color='black',
        text_align='l',
        line_height=1.1
    ):
        if isinstance(content, str):
            content = [content]
        
        self.content = content
        self.style = dict(
            font_family = font_family,
            font_size = font_size,
            font_weight = font_weight,
            font_style = font_style
        )

        if color != 'black':
            self.style['color'] = color

        self.width = width
        self.height = height
        self.text_align = text_align
        self.line_height = line_height

        self.stream = ''
        self.line = []
        self.line_spaces = {}
        self.word = ''
        self.word_width = self.line_width = self.current_height = 0
        self.next_extra_height = self.extra_height = self.last_indent = 0
        self.max_size = 0
        self.line_depth = None

        self.used_fonts = set([('Helvetica', 'n')])
        self.fonts = fonts

    def process(self):
        return self.process_content({'n': self.content, 'style': self.style},
            copy.deepcopy(self.style))

    def is_element_valid(self, element):
        error = ValueError(ELEMENT_ERROR.format(element))
        if not isinstance(element, dict):
            raise error

        keys = set(element.keys())
        keys.discard('style')
        if len(keys) != 1 or not keys.pop() in ['n', 'i', 'b']:
            raise error

    def build_line(self, factor=0):
        line = ''
        for el in self.line:
            if isinstance(el, dict):
                if factor != 0:
                    line += ' {} Tw'.format(el['space'] *(factor-1))
                line += '({})Tj'.format(el['text'])
            else:
                line += ' ' + el

        return line

    def add_line(self, ignore_justify=False):
        line_height = (self.max_size + self.extra_height) * self.line_height

        space_width = self.get_char_size(' ')

        if self.current_height + line_height > self.height: return 0
        code = 1

        line_instrucs = ' {{:.3f}} -{:.3f} Td{{}}'.format(line_height)

        if self.text_align == 'j':
            spaces_width = 0
            for space, count in self.line_spaces.items(): spaces_width += space * count

            factor = (self.width - self.word_width - self.line_width +
                spaces_width) / (spaces_width + space_width)

            if factor > 0.7:
                self.line[-1]['text'] += ' ' + self.word
                self.word = ''
                self.word_width = 0
                self.j = self.i
                code = 2
            else:
                factor = (self.width - self.line_width + spaces_width) / spaces_width

            line = self.build_line(factor)
            self.stream += line_instrucs.format(0, line)

        elif self.text_align == 'l':
            line = self.build_line()
            self.stream += line_instrucs.format(0, line)
        elif self.text_align == 'r':
            indent_ = self.width - self.line_width
            indent = indent_ - self.last_indent
            self.last_indent = indent_

            line = self.build_line()
            self.stream += line_instrucs.format(indent, line)
        elif self.text_align == 'c':
            indent_ = (self.width - self.line_width)/2
            indent = indent_ - self.last_indent
            self.last_indent = indent_

            line = self.build_line()
            self.stream += line_instrucs.format(indent, line)

        self.current_height += line_height
        self.line = []
        self.line_width = 0
        if self.word_width > 0:
            self.line = [{'space': space_width, 'text': self.word}]
            self.line_width = self.word_width
            self.word = ''
            self.word_width = 0
        
        self.line_spaces = {}
        self.extra_height = self.next_extra_height
        self.next_extra_height = 0
        self.max_size = self.size
        return code

    def add_content(self, content, index):
        self.i = 0; self.j = 0

        def add_line():
            ret = self.add_line()
            if ret == 0: return ret
            nonlocal last_space
            last_space = False
            self.last_line_info = [index, content[self.j:]]
            self.line_depth = 0
            return ret

        space_width = self.get_char_size(' ')
        self.line.append({'space': space_width, 'text': ''})
        last_space = False
        n_content = len(content)
        while self.i <= n_content:
            last_word = self.i == n_content
            char = None if last_word else content[self.i]
            if last_word or char.isspace():
                if char == '\r':
                    pass
                elif self.line_width + space_width + self.word_width > self.width:
                    ret = add_line()
                    if ret == 0: return True
                    if char == '\n' and ret == 1:
                        add_line()
                else:
                    if len(self.line) == 0:
                        self.line.append({'space': space_width, 'text': ''})
                    if last_space:
                        self.line[-1]['text'] += ' '
                        self.line_spaces[space_width] = \
                            self.line_spaces.get(space_width, 0) + 1
                        self.line_width += space_width

                    self.line[-1]['text'] += self.word
                    self.line_width += self.word_width
                    last_space = True
                    self.word = ''
                    self.word_width = 0
                    self.j = self.i
                    if char == '\n':
                        add_line()
            else:
                self.word_width += self.get_char_size(char)
                if char in ['(', ')']:
                    char = '\\' + char
                self.word += char

            self.i += 1

    def get_char_size(self, char):
        return self.size * self.font['widths'][char] / 1000

    def process_content(self, element, inherited, root=True):
        self.is_element_valid(element)

        style = copy.deepcopy(element.get('style', {}))
        if 'b' in element and not 'font_weight' in style:
            style['font_weight'] = 'bold'
            contents = element['b']; tag_name = 'b'
        elif 'i' in element and not 'font_style' in style:
            style['font_style'] = 'oblique'
            contents = element['i']; tag_name = 'i'
        elif 'n' in element:
            contents = element['n']; tag_name = 'n'

        f_weight = style.get('font_weight', inherited['font_weight'])
        f_style = style.get('font_style', inherited['font_style'])

        if f_weight == 'bold' and f_style in ['italics', 'oblique']:
            font_mode = 'bi'
        elif f_weight == 'bold':
            font_mode = 'b'
        elif f_style in ['italics', 'oblique']:
            font_mode = 'i'
        else:
            font_mode = 'n'

        f_family = style.get('font_family', inherited['font_family'])
        f_size = style.get('font_size', inherited['font_size'])
        f_font = self.fonts[f_family][font_mode]

        self.size = f_size
        self.font = f_font

        if any(e in style for e in ['font_size', 'font_family', 'font_weight', 'font_style']):
            self.used_fonts.add((f_family, font_mode))
            font_name = self.font['ref']
            self.line.append('/{} {} Tf'.format(font_name, self.size))

            if self.size > self.max_size:
                self.max_size = self.size
        if 'color' in style:
            self.line.append(pdf_color(style['color'], False))
        if 'rise' in style:
            amount = self.size*style['rise']
            self.line.append('{} Ts'.format(amount))
            if amount < 0 and -amount > self.next_extra_height:
                self.next_extra_height = -amount
            elif amount + self.size > self.max_size:
                self.max_size = amount + self.size

        inherited.update(style)

        n_contents = len(contents)
        if not self.line_depth is None:
            self.line_depth += 1
        i = 0
        for i, content in enumerate(contents):
            if isinstance(content, str):
                ret = self.add_content(content, i)
            else:
                self.line.append('q')
                ret = self.process_content(content, inherited, False)
                self.size = f_size
                self.font = f_font
                self.line.append('Q')

            if ret is None:
                pass
            elif isinstance(ret, bool) and ret:
                if self.line_depth > 0:
                    self.line_depth -= 1
                    self.stream += ' Q'
                    return True
                else:
                    index, text = self.last_line_info
                    element[tag_name] = [text]
                    if index + 1 < n_contents:
                        element[tag_name] += contents[index + 1:]
                    return element
            else:
                element[tag_name] = [ret]
                if i + 1 < n_contents:
                    element[tag_name] += contents[i + 1:]
                return element

        if root and len(self.line) > 0:
            ret = self.add_line(True)
            if ret == 0:
                element[tag_name] = [self.last_line_info[1]]
                return element

        else:
            if not self.line_depth is None:
                self.line_depth -= 1
