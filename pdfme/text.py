import copy
import re
from .color import PDFColor
from .utils import parse_style_str


class PDFText:
    def __init__(self, content, fonts,
        width = 200,
        height = 200,
        text_align = 'l',
        line_height = 1.1,
        indent = 0,
        list_style = None
    ):

        self.style = {'f': 'Helvetica', 'c': 0.1, 's': 11, 'r':0, 'bg': None}

        if isinstance(content, str):
            content = {'s': {}, 't': [content]}
        elif isinstance(content, (list, tuple)):
            content = {'s': {}, 't': content}
        elif isinstance(content, dict):
            self.style.update(content.get('s', {}))

        self.used_fonts = set([])
        self.fonts = fonts

        if not list_style is None:
            if isinstance(list_style, str):
                if list_style == 'disc':
                    list_style = {'text': chr(108) + ' ', 'family': 'ZapfDingbats'}
                elif list_style == 'square':
                    list_style = {'text': chr(110) + ' ', 'family': 'ZapfDingbats'}
                else:
                    raise ValueError('Unknown list style: {}'.format(list_style))

            if not isinstance(list_style, dict):
                raise TypeError('List style must be a str or dict: {}'.format(list_style))

            list_text = list_style.get('text')
            list_family = list_style.get('family', self.style['f'])
            style = self.style.copy()
            style['f'] = list_family
            state = self.get_state(style)
            state['s'] *= 0.7
            font = [state['f'], state['m'], state['s']]
            list_txt_width = sum(self.get_char_size(l, font) for l in list_text)
            space = self.get_char_size(' ', font)
            self.list_style = {'text': list_text, 'state': state, 'space': space}
            self.par_indent = list_txt_width + space
            width -= self.par_indent
        else:
            self.list_style = None
            self.par_indent = 0

        self.content = content

        self.width = width
        self.height = height
        self.text_align = text_align
        self.line_height = line_height

        self.last_state = {}
        self.state = {}

        self.stream = ''
        self.lines = []
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
        self.remaining = None
        self.labels = {}
        self.refs = {}
        self.current_label = None
        self.current_ref = None
        self.last_line_info = None
        self.first_line = True


    def process(self):
        self.remaining = self.process_content(self.content, True)
        return self.remaining


    def add_last_space(self, element):
        if (isinstance(element.get('t'), str) and len(element['t']) > 0
            and element['t'][-1] != ' '
        ):
            element['t'] += ' '
        elif len(element.get('t', [])) > 0:
            if isinstance(element['t'][-1], str):
                if len(element['t'][-1]) > 0 and element['t'][-1][-1] != ' ':
                    element['t'][-1] += ' '
            else:
                self.add_last_space(element['t'][-1])


    def process_content(self, element, root=False):
        style, contents = element.get('s', {}), element.get('t', [])
        if isinstance(style, str):
            style = parse_style_str(style, self.fonts)
        self.style.update(style)
        current_style = copy.deepcopy(self.style)

        rm_ref = False

        if not element.get('l') is None and self.current_label is None:
            self.current_label = element['l']
        if not element.get('r') is None and self.current_ref is None:
            self.current_ref = {'name': element['l'], 'parts': []}
            rm_ref = True

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
                if self.line_depth and self.line_depth > 0:
                    self.line_depth -= 1
                    return True
                elif self.last_line_info:
                    index, text = self.last_line_info
                    element_ = {'s': style, 't': [text]}
                    if index + 1 < n_contents:
                        element_['t'].extend(contents[index + 1:])
                    return element_
                else:
                    return ''
            else:
                element_ = {'s': style, 't': [ret]}
                if i + 1 < n_contents:
                    element_['t'].extend(contents[i + 1:])
                return element_

        if rm_ref:
            self.current_ref = None

        if root and len(self.line) > 0:
            ret = self.add_line(content, i, True)
            if ret == 0:
                return {'s': style, 't': [self.last_line_info[1]]}
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

        x = round(indent, 3)
        if x == 0: x = 0

        if self.first_line:
            self.first_line = False
            if self.list_style:
                self.used_fonts.add((self.list_style['state']['f'],
                    self.list_style['state']['m']))
                list_text = self.build_word(self.list_style['text'],
                    self.list_style['space'], self.list_style['state'])
                self.stream += ' 0 -{} Td{} {} 0 Td{}'.format(
                    round(line_height, 3), list_text, x + self.par_indent, line)
                self.lines.append({'indent': x, 'line_height': line_height,
                    'text': line})
            else:
                self.stream += ' {} -{} Td{}'.format(x, round(line_height, 3), line)
                self.lines.append({'indent': x, 'line_height': line_height,
                    'text': line})
        else:
            self.stream += ' {} -{} Td{}'.format(x, round(line_height, 3), line)
            self.lines.append({'indent': x, 'line_height': line_height,
                'text': line})

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


    def get_state(self, style):
        state = {}
        state['f']  = style['f']

        f_mode = ''
        if style.get('b', False): f_mode += 'b'
        if style.get('i', False): f_mode += 'i'
        if f_mode == '': f_mode = 'n'
        state['m'] = 'n' if not f_mode in self.fonts[state['f']] else f_mode

        state['s'] = style['s']
        state['c'] = PDFColor(style['c'])
        state['bg'] = PDFColor(style.get('bg'))
        state['r'] = style.get('r') * state['s']
        state['u'] = style.get('u', False)

        return state

    def set_state(self):
        self.last_state = self.state
        self.state = self.get_state(self.style)
        self.current_state = {}

        self.space_width = self.get_char_size(' ')

        if (self.state['f'] != self.last_state.get('f') or
            self.state['m'] != self.last_state.get('m') or
            self.state['s'] != self.last_state.get('s')
        ):
            self.current_state['f'] = self.state['f']
            self.current_state['m'] = self.state['m']
            self.current_state['s'] = self.state['s']

            self.used_fonts.add((self.state['f'], self.state['m']))

        if self.state['c'] != self.last_state.get('c'):
            self.current_state['c'] = self.state['c']

        if self.state['bg'] != self.last_state.get('bg'):
            self.current_state['bg'] = self.state['bg']

        last_rise = self.last_state.get('r')
        if self.state['r'] != last_rise:
            self.current_state['r'] = self.state['r']

        self.init_state = True


    def init_word(self):
        if len(self.word) == 0 or self.init_state:
            word = {'space': self.space_width, 'text': '', 'state': self.state}

            if not self.current_label is None:
                word['state']['label'] = self.current_label
                self.current_label = None

            if not self.current_ref is None:
                word['state']['ref'] = self.current_ref

            if self.init_state:
                word['c_state'] = self.current_state
                self.init_state = False
            self.word.append(word)

    
    def word_to_line(self):
        self.line_words.extend([
            {'text': w['text'], 'state': w['state']} for w in self.word
        ])

        if (len(self.line) > 0 and len(self.word) > 0
            and self.word[0].get('c_state') is None
        ):
            self.line[-1]['text'] += self.word[0]['text']
            self.word = self.word[1:]

        for w in self.word:
            size = w['state']['s'] if w['state'].get('r',0) >= 0 \
                else w['state']['s'] + w['state'].get('r',0)
            if size > self.max_size:
                self.max_size = size
            self.rise_effects(w['state']['r'])

        if self.state['s'] > self.max_size:
            self.max_size = self.state['s']

        self.line.extend(self.word)
        self.line_width += self.word_width
        self.word = []
        self.word_width = 0


    def build_word(self, text, space, state, factor=1):
        word = ''
        s = state
        if 'f' in s:
            word += ' /{} {} Tf'.format(
                self.fonts[s['f']][s['m']]['ref'], round(s['s'],3))
        if 'c' in s:
            word += ' ' + str(s['c'])
        if 'r' in s:
            word += ' {} Ts'.format(round(s['r'], 3))

        tw = round(space * (factor-1), 3)
        if tw == 0: tw = 0
        word += ' {} Tw'.format(tw)
        if text != '':
            word += ' ({})Tj'.format(text)

        return word


    def build_line(self, factor=1):
        line = ''
        for el in self.line:
            line += self.build_word(el['text'], el['space'],
                el.get('c_state', {}), factor)
        return line


    def build_decorators(self, factor, indent, line_height):
        base = self.current_height + line_height
        x = indent
        for el in self.line_words:
            s = el['state']

            x2 = x + factor * el['space'] if 'space' in el else x + sum(
                self.get_char_size(l, [s['f'], s['m'], s['s']]) for l in el['text']
            )

            if not s.get('label') is None:
                self.labels[s.get('label')] = {'x': x, 'y': base - s['s']}

            if not s.get('ref') is None:
                self.refs.setdefault(s['ref'], [])
                ref = self.refs[s['ref']]
                y = base - s['r'] + s['s']*0.25
                if (len(ref) > 0
                    and y == ref[-1]['y']
                    and s['s'] == ref[-1]['h']
                    and ref[-1]['x2'] == x
                ):
                    ref[-1]['x2'] = x2
                else:
                    ref.append({'x1': x, 'x2': x2, 'y': y, 'h': s['s']})

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

        for label in self.labels.values():
            label['x'] = round(x + label['x'], 3)
            label['y'] = round(y - label['y'], 3)

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
                stream += ' {} w'.format(round(last_width, 3))

            y_ = y - underline['y']
            stream += ' {} {} m {} {} l S'.format(round(x + underline['x1'],3),
                round(y_, 3), round(x + underline['x2'], 3), round(y_, 3)
            )

        stream += ' BT 1 0 0 1 {} {} Tm{} ET'.format(x, y, self.stream)
        return stream


    def get_char_size(self, char, font_state=None):
        if font_state:
            f, m, s = font_state
            return s * self.fonts[f][m]['widths'][char] / 1000
        else:
            return self.state['s'] * self.font['widths'][char] / 1000


    @property
    def font(self):
        return self.fonts[self.state['f']][self.state['m']]

