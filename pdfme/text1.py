import re
from .color import PDFColor
from .utils import parse_style_str, default

PARAGRAPH_DEFAULTS = {'height': 200, 'width': 200, 'text_align': 'l',
    'indent': 0, 'list_style': None}

TEXT_DEFAULTS = {'f': 'Helvetica', 'c': 0.1, 's': 11, 'r':0, 'bg': None}

class PDFWord:
    def __init__(self, word, parent_position, word_position):
        self.word = word
        self.parent_position = parent_position
        self.word_position = word_position

    def __str__(self):
        return self.word

class PDFState:
    def __init__(self, fonts, style):

        self.fonts = fonts

        self.font_family  = style['f']

        f_mode = ''
        if style.get('b', False): f_mode += 'b'
        if style.get('i', False): f_mode += 'i'
        if f_mode == '': f_mode = 'n'
        self.font_mode = 'n' if not f_mode in fonts[style['f']] else f_mode

        self.size = style['s']
        self.color = PDFColor(style['c'])
        self.rise = style.get('r') * self.size

    def output(self, other):
        ret_value = ''
        if (other is None or
            self.font_family != other.font_family or
            self.font_mode != other.font_mode or
            self.size != other.size
        ):
            ret_value += ' /{} {} Tf'.format(
                self.fonts[self.font_family][self.font_mode]['ref'],
                round(self.size, 3)
            )
        if other is None or self.color != other.color:
            ret_value += ' ' + str(self.color)
        if other is None or self.rise != other.rise:
            ret_value += ' {} Ts'.format(round(self.rise, 3))

        return ret_value


class PDFTextLinePart:
    def __init__(self, fonts, style, label=None, ref=None):

        self.fonts = fonts

        self.state = PDFState(fonts, style)
        self.underline = style.get('u', False)
        self.background = PDFColor(style.get('bg'))
        self.label = label
        self.ref = ref

        self.width = 0
        self.words = []

        self.space_width = self.get_char_width(' ')
        self.spaces_width = 0

    def pop_last_word(self):
        if len(self.words) > 0: return self.words.pop()
        else: return None

    def add_word(self, word):
        self.words.append(word)
        word_ = str(word)
        if word_ == ' ':
            self.spaces_width += self.space_width
        else:
            self.width += self.get_word_width(word_)

    def current_width(self, factor=1):
        return self.width + self.spaces_width*factor

    def tentative_width(self, word, factor=1):
        word_width = self.space_width * factor if word == ' ' else \
            self.get_word_width(word)
        return self.current_width(factor) + word_width

    def get_char_width(self, char):
        return self.state.size * self.fonts[self.state.font_family]\
            [self.state.font_mode]['widths'][char] / 1000

    def get_word_width(self, word):
        width = 0
        for char in word: width += self.get_char_width(char)
        return width

    def output(self, factor=1):
        stream = ''
        text = ''.join(str(word) for word in self.words)
        if text != '':
            stream += ' ({})Tj'.format(text)

        return stream

class PDFTextLine:
    def __init__(self, fonts, max_width=0, text_align=None, line_height=None,
        top_margin=0
    ):
        self.fonts = fonts
        self.max_width = max_width
        self.line_parts = []

        self.justify_min_factor = 0.7
        self.current_width = 0

        self.text_align = default(text_align, PARAGRAPH_DEFAULTS['text_align'])
        self.line_height = default(line_height, PARAGRAPH_DEFAULTS['line_height'])

        self.top_margin = top_margin

    @property
    def height(self):
        top = 0
        height_ = 0
        for part in self.line_parts:
            if part.state.rise > 0 and part.state.rise > top:
                top = part.state.rise
            if part.state.size > height_:
                height_ = part.state.size
        
        return height_*self.line_height + self.top_margin + top

    def get_width(self):
        words_width = 0
        spaces_width = 0
        for part in self.line_parts:
            words_width += part.width
            spaces_width += part.spaces_width
        return words_width, spaces_width

    def get_factor(self):
        return 1 if self.text_align != 'j' else self.justify_min_factor

    def add_line_part(self, line_part=None, style=None, label=None, ref=None):
        if len(self.line_parts) > 0:
            factor = self.get_factor()
            self.current_width += self.line_parts[-1].current_width(factor)

        if line_part is None:
            if style is None:
                raise Exception('To add a line part to a line you have to '
                    'provide wheter an existing line_part, or style (mandatory)'
                    ' and optionally label and ref with it.'
                )
            line_part = PDFTextLinePart(self.fonts, style, label, ref)



        self.line_parts.append(line_part)
        return line_part

    def add_word(self, word):
        if len(self.line_parts) == 0:
            raise Exception('You have to add a line_part, using method '
                '"add_line_part" to this line, before adding a word'
            )
        word_ = str(word)
        current_line_part = self.line_parts[-1]
        factor = self.get_factor()
        tentative_width = current_line_part.tentative_width(word_, factor)
        if self.current_width + tentative_width < self.max_width:
            current_line_part.add_word(word)
        else:
            new_line_parts = []
            if word_ != ' ':
                current_line_part.add_word(word)
                for i in range(len(self.line_parts) - 1, 0, -1):
                    line_part = self.line_parts[i]
                    words = line_part.words
                    prev_words = self.line_parts[i - 1].words

                    if len(words) == 1 and str(words[0]) != ' ':
                        if str(prev_words[-1]) if len(prev_words) else None == ' ':
                            new_line_parts.insert(0, self.line_parts.pop(i))
                            break
                        else:
                            new_line_parts.insert(0, line_part)
                    else:
                        new_line_part = PDFTextLinePart(self.fonts,
                            line_part.style,
                            line_part.label,
                            line_part.ref
                        )
                        line_part.pop_last_word()
                        new_line_part.add_word(word)
                        new_line_parts.append(new_line_part)
                        break

            bottom = 0
            for part in self.line_parts:
                if part.state.rise < 0 and -part.state.rise > bottom:
                    bottom = -part.state.rise

            new_text_line = PDFTextLine(self.fonts, self.max_width,
                self.text_align, self.line_height, bottom)
            
            for line_part in new_line_parts:
                new_text_line.add_line_part(line_part=line_part)

            return new_text_line

class PDFText:
    def __init__(self, content, fonts,
        width = None,
        height = None,
        text_align = None,
        line_height = None,
        indent = None,
        list_style = None
    ):
        self.fonts = fonts

        self.width = default(width, PARAGRAPH_DEFAULTS['width'])
        self.height = default(height, PARAGRAPH_DEFAULTS['height'])
        self.indent = default(indent, PARAGRAPH_DEFAULTS['indent'])
        self.text_align = default(text_align, PARAGRAPH_DEFAULTS['text_align'])
        self.line_height = default(line_height, PARAGRAPH_DEFAULTS['line_height'])
        self.list_style = default(list_style, PARAGRAPH_DEFAULTS['list_style'])

        self.current_height = 0

        self.current_line = PDFTextLine(self.fonts, self.width,
                    self.text_align, self.line_height)

        self.lines = []
        self.labels = {}
        self.refs = {}

        if isinstance(content, str): content = {'.': [content]}
        elif isinstance(content, (list, tuple)): content = {'.': content}

        if not isinstance(content, dict):
            raise TypeError(
                'content must be of type dict, str, list or tuple: {}'
                .format(content)
            )

        self.last_position = None

        self.remaining = None
        self.content = content

    def run(self):
        text_part = PDFTextPart(self.content, self, [])
        interrupted = text_part.run()
        if interrupted:
            self.set_remaining()
        return self.remaining

    def set_remaining(self):
        if self.last_position:
            self.remaining = self.content.copy()
            parent_position, word_position = self.last_position
            content = self.remaining
            for position in parent_position[:-1]:
                for key, value in content.items():
                    if key.startswith('.'):
                        if isinstance(value, str): value = [value]
                        content[key] = value[position:]
                        element = value[position]
                        if isinstance(element, dict):
                            content[key][0] = element.copy()
                            content = content[key][0]
                        if isinstance(element, str):
                            content[key][0] = element[word_position:]         
        else:
            self.remaining = self.content

    def build(self, x, y):
        self.stream = ''

        y_ = y

        graphics = ''
        text = ''

        last_indent = 0
        last_state = None
        last_factor = None
        last_fill = None
        last_color = None
        last_width = None

        for line in self.lines:
            line_stream = ' '

            line_height = line.height 
            full_line_height = line_height * self.line_height
            y_ -= full_line_height

            words_width, spaces_width = line.get_width()
            line_width = words_width + spaces_width
            factor = 1 if self.text_align != 'j' else \
                (self.width - line_width) / spaces_width

            if self.text_align in ['r', 'c']:
                indent = self.width - line_width
                if self.text_align == 'c': indent /= 2
                adjusted_indent = indent - last_indent
                last_indent = indent

            x_ = x + indent

            for part in line.line_parts:
                line_stream += part.state - last_state
                last_state = part.state

                tw = round(part.space_width * factor, 3)
                if last_factor != tw:
                    if tw == 0: tw = 0
                    line_stream += ' {} Tw'.format(tw)
                    last_factor = tw

                line_stream += part.output()

                x_round = round(x_, 3)

                part_width = part.current_width(factor)
                part_width_ = round(part_width, 3)
                part_size = round(part.state.size, 3)
                part_rise = part.state.rise

                if part.label is not None:
                    self.labels[part.label] = {'x': x_round,
                        'y': round(y_ + part_size, 3)}

                y_ref = round(y_ - part_rise + part_size*0.25, 3)

                if part.ref is not None:
                    ref = self.refs.setdefault(part.ref, [])
                    ref.append({'x': x_round, 'y': y_ref,
                        'w': part_width_, 'h': part_size})

                if part.background is not None and not part.background.color is None:
                    if part.background != last_fill:
                        last_fill = part.background
                        graphics += ' ' + str(last_fill)

                    graphics += ' {} {} {} {} re F'.format(x_round, y_ref,
                        part_width_, part_size)

                if part.underline:
                    color = PDFColor(part.state.color)
                    color.stroke = True
                    line_width = part.state.size * 0.1
                    y_u = round(y_ - part_rise + line_width, 3)

                    if color != last_color:
                        last_color = color
                        graphics += ' ' + str(last_color)

                    if line_width != last_width:
                        last_width = line_width
                        graphics += ' {} w'.format(round(last_width, 3))

                    graphics += ' {} {} m {} {} l S'.format(x_round, y_u,
                        round(x_ + part_width, 3), y_u)

                x_ += part_width

            text += ' {} -{} Td{}'.format(adjusted_indent,
                round(full_line_height, 3), line_stream)

        self.stream = '{} BT 1 0 0 1 {} {} Tm{} ET'.format(graphics, x, y, text)
        return self.stream

    def get_last_word(self, line):
        for line_part in reversed(line.line_parts):
            if len(line_part.words):
                return line_part.words[-1]

    def add_word(self, word):
        new_line = self.current_line.add_word(word)
        if new_line is not None:
            line_height = self.current_line.height * self.line_height
            if line_height + self.current_height > self.height:
                return True
            else:
                last_word = self.get_last_word(new_line)
                if not last_word:
                    last_word = self.get_last_word(self.current_line)
                
                self.last_position = [last_word.parent_position,
                    last_word.word_position]

                self.current_height += line_height
                self.lines.append(self.current_line)
                self.current_line = new_line

        return False

class PDFTextPart:
    def __init__(self, content, root, position, parent=None):
        self.parent = parent
        self.position = position
        self.root = root

        self.style = TEXT_DEFAULTS.copy()
        self.style.update(self.parent.style if self.parent else {})
        self.elements = []
        for key, value in content.items():
            if key.startswith('.'):
                self.style.update(parse_style_str(key[1:], self.root.fonts))
                if isinstance(value, str): value = [value]
                if not isinstance(value, (list, tuple)):
                    raise TypeError('value of .* attr must be of type str, list'
                        ' or tuple: {}'.format(value))
                self.elements = value
                break

        self.style.update(content.get('style', {}))
        self.label = content.get('label', None)
        self.ref = content.get('ref', None)

        self.init = False
        self.add_line_part = True

    def run(self):
        for i, element in enumerate(self.elements):
            if isinstance(element, str) and element != '':
                should_stop = self.process(element, i)
                if should_stop:
                    return True
            elif isinstance(element, dict):
                position = self.position.copy()
                position.append(i)
                text_part = PDFTextPart(element, self.root, position, self)
                should_stop = text_part.run()
                if should_stop:
                    return True
                self.add_line_part = True
            else:
                raise TypeError(
                    'elements must be of type str or dict: {}'.format(element)
                )
        return False

    def process(self, text, index):
        if self.add_line_part:
            line = self.root.current_line
            line.add_line_part(style=self.style, label=self.label, ref=self.ref)
            self.add_line_part = False

        words = re.split('([ \n\r\t])', text)
        should_return = False
        i = 0
        for word in words:
            j = i + len(word)
            if word == '\r': continue
            elif word == '\n': continue
            elif word == ' ' or word == '\t': word = ' '

            position = self.position.copy(); position.append(index)
            word_ = PDFWord(word, position, i)
            i = j
            should_return = self.root.add_word(word_)
            if should_return: return True 

        return False