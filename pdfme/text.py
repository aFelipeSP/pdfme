from copy import deepcopy
import re
from .color import PDFColor
from .utils import parse_style_str, default, process_style
from .standard_fonts import STANDARD_FONTS

PARAGRAPH_DEFAULTS = {'height': 200, 'width': 200, 'text_align': 'l',
                      'line_height': 1.1, 'indent': 0}

TEXT_DEFAULTS = {'f': 'Helvetica', 'c': 0.1, 's': 11, 'r': 0, 'bg': None}


class PDFState:
    def __init__(self, style, fonts=None):

        self.fonts = STANDARD_FONTS if fonts is None else fonts

        self.font_family = style['f']

        f_mode = ''
        if style.get('b', False):
            f_mode += 'b'
        if style.get('i', False):
            f_mode += 'i'
        if f_mode == '':
            f_mode = 'n'
        self.font_mode = 'n' if not f_mode in fonts[style['f']] else f_mode

        self.size = style['s']
        self.color = PDFColor(style['c'])
        self.rise = style.get('r', 0) * self.size

    def __sub__(self, other):
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
    def __init__(self, style, fonts=None, label=None, ref=None, uri=None):

        self.fonts = STANDARD_FONTS if fonts is None else fonts

        self.style = style
        self.state = PDFState(fonts, style)
        self.underline = style.get('u', False)
        self.background = PDFColor(style.get('bg'))
        self.label = label
        self.ref = ref
        self.uri = uri

        self.width = 0
        self.words = []

        self.space_width = self.get_char_width(' ')
        self.spaces_width = 0

    def pop_word(self, index=None):
        if len(self.words) > 0:
            word = str(self.words.pop()
                       if index is None else self.words.pop(index))
            if word == ' ':
                self.spaces_width -= self.space_width
            else:
                self.width -= self.get_word_width(word)
            return word

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
        return self.state.size * self.fonts[self.state.font_family][self.state.font_mode]['widths'][char] / 1000

    def get_word_width(self, word):
        return sum(self.get_char_width(char) for char in word)

    def output_text(self, last_state, last_factor, factor):
        stream = self.state - last_state

        tw = round(self.space_width * (factor - 1), 3)
        if last_factor != tw:
            if tw == 0:
                tw = 0
            stream += ' {} Tw'.format(tw)
            last_factor = tw

        text = ''.join(str(word) for word in self.words)
        if text != '':
            stream += ' ({})Tj'.format(text)

        return stream, self.state, last_factor

    def output_graphics(self, x, y, last_fill, last_color, last_stroke_width,
                        part_width
                        ):
        graphics = ''
        if self.background is not None and not self.background.color is None:
            if self.background != last_fill:
                last_fill = self.background
                graphics += ' ' + str(last_fill)

            graphics += ' {} {} {} {} re F'.format(round(x, 3),
                                                   round(
                                                       y + self.state.rise - self.state.size, 3*0.25, 3),
                                                   round(part_width, 3), round(
                                                       self.state.size, 3)
                                                   )

        if self.underline:
            color = PDFColor(self.state.color, True)
            stroke_width = self.state.size * 0.1
            y_u = round(y + self.state.rise - stroke_width, 3)

            if color != last_color:
                last_color = color
                graphics += ' ' + str(last_color)

            if stroke_width != last_stroke_width:
                last_stroke_width = stroke_width
                graphics += ' {} w'.format(round(last_stroke_width, 3))

            graphics += ' {} {} m {} {} l S'.format(round(x, 3), y_u,
                                                    round(x + part_width, 3), y_u)

        return graphics, last_fill, last_color, last_stroke_width


class PDFTextLine:
    def __init__(
            self, fonts=None, max_width=0, text_align=None, line_height=None,
            top_margin=0
        ):
        self.fonts = STANDARD_FONTS if fonts is None else fonts
        self.max_width = max_width
        self.line_parts = []

        self.justify_min_factor = 0.7

        self.text_align = default(text_align, PARAGRAPH_DEFAULTS['text_align'])
        self.line_height = default(
            line_height, PARAGRAPH_DEFAULTS['line_height']
        )

        self.top_margin = top_margin
        self.aux_line = None

    @property
    def height(self):
        top = 0
        height_ = 0
        for part in self.line_parts:
            if part.state.rise > 0 and part.state.rise > top:
                top = part.state.rise
            if part.state.size > height_:
                height_ = part.state.size

        return height_ + self.top_margin + top

    @property
    def min_width(self):
        ws = self.get_widths()
        return ws[0] + ws[1] * self.factor

    @property
    def factor(self):
        return 1 if self.text_align != 'j' else self.justify_min_factor

    @property
    def bottom(self):
        bottom = 0
        for part in self.line_parts:
            if part.state.rise < 0 and -part.state.rise > bottom:
                bottom = -part.state.rise
        return bottom

    def get_widths(self):
        words_width = 0
        spaces_width = 0
        for part in self.line_parts:
            words_width += part.width
            spaces_width += part.spaces_width
        return words_width, spaces_width

    def add_line_part(self, line_part=None, style=None,
                      label=None, ref=None, uri=None
                      ):
        if len(self.line_parts) > 0:
            self.current_width += self.line_parts[-1].current_width(self.factor)

        if line_part is None:
            if style is None:
                raise Exception('To add a line part to a line you have to '
                                'provide whether an existing line_part, or a style'
                                ' and optionally label, ref and uri with it.'
                                )
            line_part = PDFTextLinePart(self.fonts, style, label, ref, uri)

        self.line_parts.append(line_part)
        return line_part


    def add_word(self, word):
        if len(self.line_parts) == 0:
            raise Exception(
                'You have to add a line_part, using method "add_line_part" to '
                'this line, before adding a word'
            )

        if word == ' ':
            if self.aux_line is not None:
                self.aux_line.line_parts[-1].add_word(' ')
                self.line_parts.extend(self.aux_line.line_parts)
                self.aux_line.line_parts = []
        else:
            if self.aux_line is None:
                self.aux_line = PDFTextLine(self.fonts, self.max_width,
                    self.text_align, self.line_height)
            self.aux_line.line_parts[-1].add_word(word)
            line_part = self.aux_line.line_parts[-1]
            tentative_width = line_part.tentative_width(word, self.factor)
            
            if (
                self.width + self.aux_line.width + tentative_width < 
                self.max_width
            ):
                current_line_part.add_word(word)
            else:
                if word_ != ' ':
                    new_line_parts = []
                    current_line_part.add_word(word)
                    for i in range(len(self.line_parts) - 1, -1, -1):
                        line_part = self.line_parts[i]
                        words = line_part.words

                        if i > 0 and len(words) == 1 and words[0] != ' ':
                            prev_words = self.line_parts[i - 1].words
                            last_word = prev_words[-1] if len(prev_words) else None
                            if last_word == ' ':
                                new_line_parts.insert(0, self.line_parts.pop(i))
                                break
                            else:
                                new_line_parts.insert(0, line_part)
                        else:
                            new_line_part = PDFTextLinePart(self.fonts,
                                                            line_part.style,
                                                            line_part.label,
                                                            line_part.ref,
                                                            line_part.uri
                                                            )
                            line_part.pop_word()
                            new_line_part.add_word(word)
                            new_line_parts.append(new_line_part)
                            break

                else:
                    new_line_parts = [PDFTextLinePart(self.fonts,
                                                    current_line_part.style,
                                                    current_line_part.label,
                                                    current_line_part.ref,
                                                    current_line_part.uri
                                                    )]

                new_text_line = PDFTextLine(self.fonts, self.max_width,
                    self.text_align, self.line_height, self.bottom)

                for line_part in new_line_parts:
                    new_text_line.add_line_part(line_part=line_part)

                return new_text_line


class PDFTextBase:
    def __init__(self, content, width, height, fonts=None, text_align=None,
                 line_height=None, indent=None, list_text=None, list_indent=None,
                 list_style=None
                 ):
        self.fonts = STANDARD_FONTS if fonts is None else fonts
        self.used_fonts = set([])

        self.width = default(width, PARAGRAPH_DEFAULTS['width'])
        self.height = max(0, default(height, PARAGRAPH_DEFAULTS['height']))
        self.indent = default(indent, PARAGRAPH_DEFAULTS['indent'])
        self.text_align = default(text_align, PARAGRAPH_DEFAULTS['text_align'])
        self.line_height = default(
            line_height, PARAGRAPH_DEFAULTS['line_height'])
        self.list_text = list_text
        self.list_indent = list_indent
        self.list_style = list_style

        self.current_height = 0
        self.current_line_used_fonts = set()
        self.lines = []
        self.current_line = PDFTextLine(
            self.fonts, self.width - self.indent, self.text_align,
            self.line_height
        )

        if isinstance(content, str):
            content = [{'s': TEXT_DEFAULTS.copy(), 't': content}]
        if not isinstance(content, (list, tuple)):
            raise TypeError(
                'content must be of type str, list or tuple: {}'
                .format(content)
            )

        self.last_part_index = 0
        self.last_word_index = 0
        self.last_word_added_index = 0

        self.content = content
        self.started = False
        self.finished = False

    def run(self):
        for part_index in range(self.last_part_index, len(self.content)):
            part = self.content[part_index]
            if not isinstance(part, dict):
                raise TypeError(
                    'elements in content must be of type dict: {}'
                    .format(part)
                )
            if 'type' in part:
                if part['type'] == 'br':
                    continue_ = self.add_current_line()
                    if continue_:
                        self.last_part_index = part_index + 1
                        self.last_word_index = 0
            else:
                action = self.add_part(part, part_index)
                if action == 'continue':
                    continue
        self.finished = True

    def add_part(self, part, part_index):
        words = part.get('t')
        if not isinstance(words, (str, list, tuple)):
            return 'continue'

        style = TEXT_DEFAULTS.copy()
        style.update(part.get('style', {}))
        new_line_part = self.current_line.add_line_part(
            style=style, ids=part.get('ids')
        )

        if not self.started:
            self.started = True
            self.setup_list()

        self.current_line_used_fonts.add((
            new_line_part.state.font_family,
            new_line_part.state.font_mode
        ))
        action = self.add_words(words, part_index)

    def add_words(self, words, part_index):
        if isinstance(words, str):
            self.content[self.current_index]['t'] = words = (
                ' ' if w.isspace() else w
                for w in re.split('( +)', words)
                if w != ''
            )
        for word_index in range(self.last_word_index, len(words)):
            word = words[word_index]
            new_line = self.current_line.add_word(word)
            if new_line is not None:
                continue_ = self.add_current_line()
                if continue_:
                    self.last_part_index = part_index + 1
                    self.last_word_index = 0

    def add_current_line(self):
        line_height = self.current_line.height * self.line_height
        if line_height + self.current_height > self.height:
            return False
        else:
            self.current_height += line_height
            # TODO: is this necesary
            self.strip_line(self.current_line)
            self.lines.append(self.current_line)
            self.used_fonts.update(self.current_line_used_fonts)
            self.current_line_used_fonts = set()
            return True

    def strip_line(self, line):
        for index in [0, -1]:
            while (
                line.line_parts and line.line_parts[index].words and
                str(line.line_parts[index].words[index]) == ' '
            ):
                line.line_parts[index].pop_word(index)

    def setup_list(self):
        if self.list_text:
            style = self.current_line.line_parts[0].style.copy()

            if self.list_style is None:
                self.list_style = {}
            elif isinstance(self.list_style, str):
                self.list_style = parse_style_str(self.list_style, self.fonts)

            if not isinstance(self.list_style, dict):
                raise TypeError('list_style must be a str or a dict. Value: {}'
                                .format(self.list_style))

            style.update(self.list_style)
            line_part = PDFTextLinePart(self.fonts, style)

            self.current_line_used_fonts.add(
                (line_part.state.font_family, line_part.state.font_mode)
            )

            if self.list_indent is None:
                self.list_indent = line_part.get_word_width(self.list_text)
            elif not isinstance(self.list_indent, (float, int)):
                raise TypeError('list_indent must be int or float. Value: {}'
                                .format(self.list_style))

            self.list_state = line_part.state
            self.current_line.max_width -= self.list_indent

    def build(self, x, y):
        graphics = ''
        text = ''
        last_indent = 0
        last_state = last_factor = last_fill = last_color = last_stroke_width = None
        lines_len = len(self.lines) - 1
        y_ = y

        for i, line in enumerate(self.lines):
            words_width, spaces_width = line.get_width()
            line_width = words_width + spaces_width
            last_line = i == lines_len and self.finished

            line_indent = self.list_indent if self.list_text else 0
            line_height = line.height
            full_line_height = line_height
            if i == 0:
                factor = 1 if self.text_align != 'j' or spaces_width == 0\
                    else (self.width - self.indent - words_width) / spaces_width

                if self.list_text:
                    if self.list_state.size > full_line_height:
                        full_line_height = self.list_state.size

                    text += ' 0 -{} Td{} ({})Tj {} 0 Td'.format(
                        round(full_line_height, 3), self.list_state -
                        last_state,
                        self.list_text, self.list_indent + self.indent)
                else:
                    text += ' {} -{} Td'.format(round(self.indent, 3),
                                                round(full_line_height, 3))
            else:
                factor = 1 if self.text_align != 'j' or last_line or spaces_width == 0\
                    else (self.width - words_width) / spaces_width

                adjusted_indent = 0
                if self.text_align in ['r', 'c']:
                    indent = self.width - line_width
                    if self.text_align == 'c':
                        indent /= 2
                    line_indent += indent
                    adjusted_indent = indent - last_indent
                    last_indent = indent

                if i == 1:
                    adjusted_indent -= self.indent

                full_line_height *= self.line_height

                text += ' {} -{} Td'.format(round(adjusted_indent, 3),
                                            round(full_line_height, 3))

            y_ -= full_line_height
            x_ = x + line_indent
            line_stream = ''

            for part in line.line_parts:
                part_stream, last_state, last_factor = part.output_text(
                    last_state, last_factor, factor)

                line_stream += part_stream

                part_width = part.current_width(factor)
                part_size = round(part.state.size, 3)

                if part.label is not None and part.label not in self.labels:
                    self.labels[part.label] = {
                        'x': round(x_, 3), 'y': round(y_ + part_size, 3)
                    }
                if part.ref is not None:
                    y_ref = y_ + part.state.rise - part_size*0.25
                    self.refs.setdefault(part.ref, []).append(
                        [round(x_, 3), round(y_ref, 3),
                         round(x_ + part_width, 3), round(y_ref + part_size, 3)
                         ])
                if part.uri is not None:
                    y_ref = y_ + part.state.rise - part_size*0.25
                    self.links.setdefault(part.uri, []).append(
                        [round(x_, 3), round(y_ref, 3),
                         round(x_ + part_width, 3), round(y_ref + part_size, 3)
                         ])

                part_graphics, last_fill, last_color, last_stroke_width = part\
                    .output_graphics(x_, y_, last_fill, last_color,
                                     last_stroke_width, part_width
                                     )

                graphics += part_graphics
                x_ += part_width

            text += line_stream

        if graphics != '':
            graphics = 'q' + graphics + ' Q '

        self.stream = ' {}BT 1 0 0 1 {} {} Tm{} ET'.format(
            graphics, round(x, 3), round(y, 3), text)
        return self.stream

    def get_last_word(self, line):
        for line_part in reversed(line.line_parts):
            if len(line_part.words):
                return line_part.words[-1]

    def strip_line(self, line):
        for index in [0, -1]:
            while (line.line_parts and line.line_parts[index].words and
                   str(line.line_parts[index].words[index]) == ' '
                   ):
                line.line_parts[index].pop_word(index)

    def add_current_line(self, new_line=None):
        cl = self.current_line
        self.current_height += cl.height * self.line_height
        self.lines.append(self.current_line)
        self.used_fonts.update(self.current_line_used_fonts)
        self.current_line_used_fonts = set()

        self.strip_line(self.current_line)

        if new_line:
            self.current_line = new_line


class PDFText:
    def __init__(self, content, fonts, width, height, text_align=None,
                 line_height=None, indent=None, list_text=None, list_indent=None,
                 list_style=None, pdf=None
                 ):
        self.fonts = fonts
        self.used_fonts = set([])

        self.width = default(width, PARAGRAPH_DEFAULTS['width'])
        self.height = max(0, default(height, PARAGRAPH_DEFAULTS['height']))
        self.indent = default(indent, PARAGRAPH_DEFAULTS['indent'])
        self.text_align = default(text_align, PARAGRAPH_DEFAULTS['text_align'])
        self.line_height = default(
            line_height, PARAGRAPH_DEFAULTS['line_height'])
        self.list_text = list_text
        self.list_indent = list_indent
        self.list_style = list_style
        self.pdf = pdf

        self.current_height = 0

        self.current_line = PDFTextLine(self.fonts, self.width - self.indent,
                                        self.text_align, self.line_height)

        self.current_line_used_fonts = set()

        self.lines = []
        self.labels = {}
        self.refs = {}
        self.links = {}

        if isinstance(content, str):
            content = {'.': [content]}
        elif isinstance(content, (list, tuple)):
            content = {'.': content}

        if not isinstance(content, dict):
            raise TypeError(
                'content must be of type dict, str, list or tuple: {}'
                .format(content)
            )

        self.last_position = None

        self.remaining = None
        self.content = content
        self.started = False

    def _new_text_part(self, style, label, ref, uri):
        text_part = {'style': style, 'label': label, 'words': []}
        self.elements.append(text_part)
        return text_part

    def _recursive_content_parse(self, content, parent_style):
        style = deepcopy(parent_style)
        elements = []
        for key, value in content.items():
            if key.startswith('.'):
                style.update(parse_style_str(key[1:], self.fonts))
                if isinstance(value, str):
                    value = [value]
                if not isinstance(value, (list, tuple)):
                    raise TypeError('value of .* attr must be of type str, list'
                                    ' or tuple: {}'.format(value))
                elements = value
                break

        style.update(process_style(content.get('style'), self.pdf))
        label = content.get('label', None)
        ref = content.get('ref', None)
        uri = content.get('uri', None)

        consecutive_strings = True
        text_part = self._new_text_part(style, label, ref, uri)

        for element in elements:
            if (isinstance(element, dict) and len(element) == 1 and
                    list(element.keys())[0] == 'var' and self.root.pdf
                ):
                element = str(self.root.pdf.context.get(element['var'], ''))

            if isinstance(element, str) and element != '':
                lines = element.split('\n')
                if not consecutive_strings:
                    text_part = self._new_text_part(style, label, ref, uri)
                text_part['words'].extend(lines[0])
                for line in lines[1:]:
                    self.elements.append({'type': 'br'})
                    text_part = self._new_text_part(style, label, ref, uri)
                    text_part['words'].extend(
                        ' ' if w.isspace() else w for w in re.split('( +)', line) if w != ''
                    )
            elif isinstance(element, dict):
                text_part = PDFTextPart(element, self.root, self)
                should_stop = text_part.run()
                if should_stop:
                    return True
                self.add_new_line_part = True
            else:
                raise TypeError(
                    'elements must be of type str or dict: {}'.format(element)
                )
        return False

    def parse_content(self, content):
        self.elements = []
        if isinstance(content, str):
            content = {'.': [content]}
        elif isinstance(content, (list, tuple)):
            content = {'.': content}

        if not isinstance(content, dict):
            raise TypeError(
                'content must be of type dict, str, list or tuple: {}'
                .format(content)
            )

        self._recursive_content_parse(content, TEXT_DEFAULTS)


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
                if isinstance(value, str):
                    value = [value]
                if not isinstance(value, (list, tuple)):
                    raise TypeError('value of .* attr must be of type str, list'
                                    ' or tuple: {}'.format(value))
                self.elements = value
                break

        self.style.update(process_style(content.get('style'), root.pdf))
        self.label = content.get('label', None)
        self.ref = content.get('ref', None)
        self.uri = content.get('uri', None)

        self.add_new_line_part = True

    def run(self):
        for i, element in enumerate(self.elements):
            if (isinstance(element, dict) and len(element) == 1 and
                    list(element.keys())[0] == 'var' and self.root.pdf
                ):
                element = str(self.root.pdf.context.get(element['var'], ''))

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
                self.add_new_line_part = True
            else:
                raise TypeError(
                    'elements must be of type str or dict: {}'.format(element)
                )
        return False

    def process(self, text, index):
        if self.add_new_line_part:
            new_line_part = self.root.current_line.add_line_part(
                style=self.style, label=self.label, ref=self.ref, uri=self.uri)

            self.root.setup_list()

            self.root.current_line_used_fonts.add(
                (new_line_part.state.font_family, new_line_part.state.font_mode)
            )
            self.add_new_line_part = False

        words = re.split('([ \n\r\t])', text)
        should_return = False
        i = 0
        for word in words:
            j = i + len(word)
            if word == '':
                continue
            elif word == '\r':
                continue
            elif word == '\n':
                continue
            elif word == ' ' or word == '\t':
                word = ' '

            position = self.position.copy()
            position.append(index)
            word_ = PDFWord(word, position, i)
            i = j
            should_return = self.root.add_word(word_)
            if should_return:
                return True

        return False
