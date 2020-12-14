import copy
import re
from .color import pdf_color, colors, PDFColor


class PDFText:
    def __init__(self, content, fonts, 
        width = 200,
        height = 200,
        text_align = 'l',
        line_height = 1.1,
        indent = 0
    ):

        self.style = {'f': 'Helvetica', 'c': 0.1, 's': 11, 'r':0, 'bg': None}

        if isinstance(content, str):
            content = {'s': {}, 'c': [content]}
        elif isinstance(content, (list, tuple)):
            content = {'s': {}, 'c': content}
        
        self.content = content

        self.add_last_space(self.content)

        self.width = width
        self.height = height
        self.text_align = text_align
        self.line_height = line_height

        self.last_state = {}
        self.state = {}

        self.stream = ''
        self.line = []
        self.line_spaces = {}
        self.line_words = []
        self.word = []
        self.word_width = self.current_height = self.max_size = 0
        self.next_extra_height = self.extra_height = self.last_indent = 0

        self.line_width = indent
        self.line_depth = None
        self.last_space = None
        self.init_state = True

        self.fills = []
        self.underlines = []

        self.indent = indent
        self.indent_mark = 0 

        self.used_fonts = set([])
        self.fonts = fonts


    def process(self):
        return self.process_content(self.content, True)


    def add_last_space(self, element):
        if (isinstance(element.get('c'), str) and len(element['c']) > 0
            and element['c'][-1] != ' '
        ):
            element['c'] += ' '
        elif len(element.get('c', [])) > 0:
            if isinstance(element['c'][-1], str):
                if len(element['c'][-1]) > 0 and element['c'][-1][-1] != ' ':
                    element['c'][-1] += ' '
            else:
                self.add_last_space(element['c'][-1])


    def parse_style_str(self,style_str):
        style = {}
        for attrs_str in style_str.split(';'):
            attrs = attrs_str.split(':')
            if len(attrs) == 0 or attrs == ['']: continue
            elif len(attrs) == 1:
                attr = attrs[0].strip()
                if not attr in ['b', 'i', 'u']:
                    raise ValueError('Style elements with no paramter must '
                        'be whether "b" for bold, "i" for italics(Oblique) or '
                        '"u" for underline.')
                style[attr] = True
            elif len(attrs) == 2:
                attr = attrs[0].strip()
                value = attrs[1].strip()
                if attr == "f":
                    if value not in self.fonts:
                        raise ValueError('Style element "f" must have the name '
                            'of a font family already added.')
                    
                    style['f'] = value
                elif attr == "c":
                    style['c'] = PDFColor(value)
                elif attr == "bg":
                    style['bg'] = PDFColor(value)
                elif attrs[0] == "s":
                    try:
                        v = float(value)
                        if int(v) == v:
                            v = int(v)
                        style['s'] = v
                    except:
                        raise ValueError('Style element value for "s" is wrong:'
                            ' {}'.format(value))
                elif attrs[0] == 'r':
                    try:
                        v = float(value)
                        style['r'] = v
                    except:
                        raise ValueError('Style element value for "r" is wrong:'
                            ' {}'.format(value))
                else:
                    raise ValueError('Style elements with parameter must be "f"'
                        ', "s", "c" or "r"')

            else:
                raise ValueError('Style elements must be "b" or "i" or '
                    '"f:<font-family>", "s:<font-size>" or "c:<font-color>"')

        return style


    def process_content(self, element, root=False):
        style, contents = element.get('s', {}), element.get('c', [])
        if isinstance(style, str):
            style = self.parse_style_str(style)
        self.style.update(style)
        current_style = copy.deepcopy(self.style)

        if isinstance(contents, str):
            contents = [contents]

        n_contents = len(contents)
        if not self.line_depth is None:
            self.line_depth += 1

        i = 0; content = None
        for i, content in enumerate(contents):
            if isinstance(content, str):
                ret = self.add_content(content, i)
            elif isinstance(content, dict):
                ret = self.process_content(content)
                self.style = copy.deepcopy(current_style)
            else:
                raise ValueError('elements must be of type str or dict: {}'.format(content))
            if ret is None:
                pass
            elif isinstance(ret, bool) and ret:
                if self.line_depth > 0:
                    self.line_depth -= 1
                    return True
                else:
                    index, text = self.last_line_info
                    element_ = {'s': style, 'c': [text]}
                    if index + 1 < n_contents:
                        element_['c'].extend(contents[index + 1:])
                    return element_
            else:
                element_ = {'s': style, 'c': [ret]}
                if i + 1 < n_contents:
                    element_['c'].extend(contents[i + 1:])
                return element_

        if root and len(self.line) > 0:
            ret = self.add_line(content, i, True)
            if ret == 0:
                return {'s': style, 'c': [self.last_line_info[1]]}
        else:
            if not self.line_depth is None:
                self.line_depth -= 1


    def add_content(self, content, index):
        self.i = 0; self.j = 0
        self.set_state()
        self.init_word()

        n_content = len(content)
        while self.i < n_content:
            char = content[self.i]
            if char.isspace():
                if char == '\r':
                    pass
                elif self.line_width + self.space_width + self.word_width > self.width:
                    ret = self.add_line(content, index)
                    if ret == 0: return True
                    if char == '\n' and ret == 1:
                        self.add_line(content, index, True)
                else:
                    if self.last_space:
                        self.line[-1]['text'] += ' '
                        self.line_words.append(self.last_space)
                        self.line_spaces[self.last_space['space']] = \
                            self.line_spaces.get(self.last_space['space'], 0) + 1
                        self.line_width += self.last_space['space']

                    self.word_to_line()
                    self.j = self.i
                    if char == '\n':
                        self.add_line(content, index, True)
                        self.last_space = None
                    else:
                        self.last_space = {'space': self.space_width, 'state': self.state}
            else:
                self.word_width += self.get_char_size(char)
                if char in ['(', ')']:
                    char = '\\' + char

                self.init_word()
                self.word[-1]['text'] += char

            self.i += 1


    def add_line(self, content, index, ignore_justify=False):
        factor = 1
        indent = 0
        indent_ = 0
        code = 1

        if self.text_align == 'j' and not ignore_justify:
            spaces_width = 0
            for space, count in self.line_spaces.items():
                spaces_width += space * count

            factor = (self.width - self.word_width - self.line_width +
                spaces_width) / (spaces_width + self.space_width)

            if factor > 0.7:
                self.line[-1]['text'] += ' '
                self.line_words.append(self.last_space)
                self.word_to_line()
                self.j = self.i
                code = 2
            else:
                factor = (self.width - self.line_width + spaces_width) / spaces_width

        elif self.text_align == 'l' or (self.text_align == 'j' and ignore_justify):
            pass
        elif self.text_align == 'r':
            indent_ = self.width - self.line_width
            indent = indent_ - self.last_indent
            self.last_indent = indent_
        elif self.text_align == 'c':
            indent_ = (self.width - self.line_width)/2
            indent = indent_ - self.last_indent
            self.last_indent = indent_

        line = self.build_line(factor)
        line_height = (self.max_size + self.extra_height) * self.line_height
        if self.current_height + line_height > self.height:
            return 0

        self.build_decorators(factor, indent_, line_height)

        if self.indent_mark == 0:
            indent += self.indent
            self.indent_mark = 1
        elif self.indent_mark == 1:
            indent -= self.indent
            self.indent_mark = 2

        self.stream += ' {:.3f} -{:.3f} Td{}'.format(indent, line_height, line)

        self.current_height += line_height
        
        self.line_spaces = {}
        self.extra_height = self.next_extra_height
        self.next_extra_height = 0

        if self.word_width > 0:
            self.line = []
            self.line_width = 0
            self.max_size = 0
            self.word_to_line()
            self.last_space = {'space': self.space_width, 'state': self.state}
        else:
            self.line = []
            self.line_width = 0
            self.max_size = self.state['s']
            self.rise_effects(self.state['r'])
            self.last_space = None

        if isinstance(content, str):
            text = content[self.j:]
            if text[0] == ' ': text = text[1:]
            self.last_line_info = [index, text]
        self.line_depth = 0

        return code

    
    def rise_effects(self, rise):
        if rise < 0 and -rise > self.next_extra_height:
            self.next_extra_height = -rise
        elif rise + self.state['s'] > self.max_size:
            self.max_size = rise + self.state['s']
    

    def set_state(self):
        self.last_state = self.state
        self.state = {}
        self.current_state = {}

        f_mode = ''
        if self.style.get('b', False): f_mode += 'b'
        if self.style.get('i', False): f_mode += 'i'
        if f_mode == '': f_mode = 'n'

        self.state['f']  = self.style['f']
        self.state['m'] = 'n' if not f_mode in self.fonts[self.state['f']] \
            else f_mode

        self.state['s'] = self.style['s']
        self.space_width = self.get_char_size(' ')

        if (self.state['f'] != self.last_state.get('f') or
            self.state['m'] != self.last_state.get('m') or
            self.state['s'] != self.last_state.get('s')
        ):
            self.current_state['f'] = self.state['f']
            self.current_state['m'] = self.state['m']
            self.current_state['s'] = self.state['s']

            self.used_fonts.add((self.state['f'], self.state['m']))
        
        self.state['c'] = PDFColor(self.style['c'])
        if self.state['c'] != self.last_state.get('c'):
            self.current_state['c'] = self.state['c']
       
        self.state['bg'] = PDFColor(self.style.get('bg'))
        if self.state['bg'] != self.last_state.get('bg'):
            self.current_state['bg'] = self.state['bg']

        self.state['r'] = self.style.get('r') * self.state['s']
        last_rise = self.last_state.get('r')
        if self.state['r'] != last_rise:
            self.current_state['r'] = self.state['r']

        self.state['u'] = self.style.get('u', False)

        self.init_state = True


    def init_word(self):
        if len(self.word) == 0 or self.init_state:
            word = {'space': self.space_width, 'text': '', 'state': self.state}
            if self.init_state:
                word['c_state'] = self.current_state
                self.init_state = False
            self.word.append(word)

    
    def word_to_line(self):
        self.line_words.extend([
            {'text': w['text'], 'state': w['state']} for w in self.word
        ])

        if (len(self.line) > 0 and len(self.word) > 0
            and self.word[0].get('c_state') == None
        ):
            self.line[-1]['text'] += self.word[0]['text']
            self.word = self.word[1:]

        self.max_size = max([w['state']['s'] for w in self.word]+[self.state['s'], self.max_size])
        for w in self.word:
            if w['text'] == 'ñláévhzku':
                print(4) 
            self.rise_effects(w['state']['r'])

        self.line.extend(self.word)
        self.line_width += self.word_width
        self.word = []
        self.word_width = 0


    def build_line(self, factor=1):
        line = ''
        for el in self.line:
            s = el.get('c_state', {})
            if 'f' in s:
                line += ' /{} {} Tf'.format(
                    self.fonts[s['f']][s['m']]['ref'], round(s['s'],3))
            if 'c' in s:
                line += ' ' + str(s['c'])
            if 'r' in s:
                line += ' {} Ts'.format(s['r'])

            line += ' {} Tw'.format(round(el['space'] * (factor-1), 4))
            if el['text'] != '':
                line += ' ({})Tj'.format(el['text'])
        return line


    def build_decorators(self, factor, indent, line_height):
        base = self.current_height + line_height
        x = indent
        for el in self.line_words:
            s = el['state']

            x2 = x + factor * el['space'] if 'space' in el else x + sum(
                s['s'] * self.fonts[s['f']][s['m']]['widths'][l] / 1000
                for l in el['text']
            )
            if not s.get('bg') is None and not s['bg'].color is None:
                y = base - s['r'] + s['s']*0.25

                if (len(self.fills) > 0
                    and y == self.fills[-1]['y']
                    and s['s'] == self.fills[-1]['h']
                    and s['bg'] == self.fills[-1]['bg']
                    and self.fills[-1]['x2'] == x
                ):
                    self.fills[-1]['x2'] = x2
                else:
                    self.fills.append({'x1': x, 'x2': x2, 'y': y,
                        'h': s['s'], 'bg': s['bg']})

            if s.get('u', False):
                color = PDFColor(s['c'])
                color.stroke = True
                line_width = s['s'] * 0.1
                y = base - s['r'] + line_width

                if (len(self.underlines) > 0
                    and y == self.underlines[-1]['y']
                    and line_width == self.underlines[-1]['w']
                    and color == self.underlines[-1]['c']
                    and self.underlines[-1]['x2'] == x
                ):
                    self.underlines[-1]['x2'] = x2
                else:
                    self.underlines.append({'x1': x, 'x2': x2, 'y': y,
                        'w': line_width, 'c': color})

            x = x2
        
        self.line_words = []


    def build(self, x, y):
        stream = ''

        last_fill = None
        for fill in self.fills:            
            if fill['bg'] != last_fill:
                last_fill = fill['bg']
                stream += ' ' + str(last_fill)

            y_ = y - fill['y']
            stream += ' {} {} {} {} re F'.format(round(x + fill['x1'],3),
                round(y_, 3), round(fill['x2'] - fill['x1'], 3), round(fill['h'], 3)
            )

        last_color = None
        last_width = None
        for underline in self.underlines:            
            if underline['c'] != last_color:
                last_color = underline['c']
                stream += ' ' + str(last_color)

            if underline['w'] != last_width:
                last_width = underline['w']
                stream += ' {} w'.format(last_width)

            y_ = y - underline['y']
            stream += ' {} {} m {} {} l S'.format(round(x + underline['x1'],3),
                round(y_, 3), round(x + underline['x2'], 3), round(y_, 3)
            )

        stream += ' BT 1 0 0 1 {} {} Tm{} ET'.format(x, y, self.stream)
        return stream


    def get_char_size(self, char):
        return self.state['s'] * self.font['widths'][char] / 1000


    def get_word_size(self, word):
        return sum(self.get_char_size(l) for l in word)


    @property
    def font(self):
        return self.fonts[self.state['f']][self.state['m']]


 

