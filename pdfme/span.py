import re
from .color import pdf_color


def paragraph(tag_list, style, fonts):
    page_width, page_height = style['page']['size']
    margins = style['page']['margin']
    if len(margins) == 1:
        margins = margins * 4
    elif len(margins) == 2:
        margins = margins * 2
    elif len(margins) == 3:
        margins = margins.append(margins[1])

    width = page_width - margins[1] - margins[3]
    height = page_height - margins[0] - margins[2]

    x = style['left']; y = style['top']

    state = {
        'stream': '',
        'line': '',
        'fonts': fonts
    }

def add_line(state):
    line_height = (state['max-size'] + state.setdefault('extra-height', 0)) * state['line-height']
    if state.setdefault('current-height', 0) + line_height > state['height']:
        return True

    check_empty_line(state)
    line = ' {{:.3f}} -{:.3f} Td{}'.format(line_height, state['line'])

    if state['text-align'] == 'j':
        pass
    elif state['text-align'] == 'l':
        state['stream'] += line.format(0)
    elif state['text-align'] == 'r':
        indent_ = state['width'] - state['current-width']
        indent = indent_ - state.get('last-indent', 0)
        state['stream'] += line.format(indent)
        state['last-indent'] = indent_
    elif state['text-align'] == 'c':
        indent_ = (state['width'] - state['current-width'])/2
        indent = indent_ - state.get('last-indent', 0)
        state['stream'] += line.format(indent)
        state['last-indent'] = indent_

    state['current-height'] += line_height


def check_empty_line(state):
    last_chars = state['line'][-2:]
    if last_chars[-2:-1] != ['\\'] and last_chars[-1:] == ['(']:
        state['line'] = state['line'][:-1]
    else:
        state['line'] += ')Tj'

def add_content(content, state, index):
    i = 0; j = 0
    state['line'] += '('
    state.setdefault('word', '')
    state.setdefault('word-width', 0)
    space_width = get_char_size(' ', state)
    last_space = False
    n_content = len(content)
    while i <= n_content:
        last_word = i == n_content
        char = None if last_word else content[i]
        if last_word or char.isspace():
            if char == '\r':
                pass
            elif state.setdefault('current-width', 0) + space_width + state['word-width'] > state['width']:
                ret = add_line(state)
                if ret:
                    return True

                state['last-line-info'] = [index, content[j:]]
                state['line-depth'] = 0

                last_space = False if last_word or char == '\n' else True

                if char == '\n':
                    pass

                state['line'] = '(' + state['word']
                state['current-width'] = state['word-width']
                state['extra-height'] = state.get('next-extra-height', 0)
                state['next-extra-height'] = 0
                state['max-size'] = state['size']

                state['word'] = ''
                state['word-width'] = 0
                
            else:
                if last_space:
                    state['line'] += ' '
                    # state['line_spaces'] += space_width
                    state['current-width'] += space_width

                state['line'] += state['word']
                state['current-width'] += state['word-width']
                last_space = True
                state['word'] = ''
                state['word-width'] = 0
                j = i
        else:
            state['word-width'] += get_char_size(char, state)
            if char in ['"', '(', ')']:
                char = '\\' + char
            state['word'] += char

        i += 1

    check_empty_line(state)

def get_char_size(char, state):
    return state['size'] * state['fonts'][state['font']]['widths'][char] / 1000

def inline_tag(contents, style, state, root=True):
    state.setdefault('line', '')
    if 'font' in style and isinstance(style['font'], (list, tuple)) and len(style['font']) == 2:
        state['line'] += ' {} {} Tf'.format(*style['font'])
        state['font'], state['size'] = style['font']
        if state['size'] > state.get('max-size', 0):
            state['max-size'] = state['size']
    if 'color' in style:
        state['line'] += ' ' + pdf_color(style['color'], False)
    if 'rise' in style:
        amount = state['size']*style['rise']
        state['line'] += ' {} Ts'.format(amount)
        if amount < 0:
            state['next-extra-height'] = max(-amount, state.get('next-extra-height', 0))
        elif amount + state['size'] > state['max-size']:
            state['max-size'] = amount + state['size']

    n_contents = len(contents)
    if state.get('line-depth'):
        state['line-depth'] += 1
    i = 0
    for i, content in enumerate(contents):
        if isinstance(content, str):
            ret = add_content(content, state, i)
        else:
            state['line'] += ' q'
            ret = inline_tag(content['content'], content['style'], state, False)
            state['font'], state['size'] = style['font']
            state['line'] += ' Q'

        if ret is None:
            pass
        elif isinstance(ret, bool) and ret:
            if state['line-depth'] > 0:
                state['line-depth'] -= 1
                state['stream'] += ' Q'
                return True
            else:
                index, text = state['last-line-info']
                ret = {'content': [text], 'style': style}
                if index + 1 < n_contents:
                    ret['content'] += contents[index + 1:]
                return ret
        else:
            ret = {'content': [ret], 'style': style}
            if i + 1 < n_contents:
                ret['content'] += contents[i + 1:]
            return ret

    if root and len(state['line']) > 0:
        state['line'] += '('
        ret = add_line(state)
        if ret:
            return {'content': [state['last-line-info'][1]], 'style': style}

    else:
        if state.get('line-depth'):
            state['line-depth'] -= 1


def parse_inline_tag(tag, style, classes):
    if tag.name in ['b', 'strong']:
        style['font-weight'] = 'bold'
    elif tag.name in ['i', 'cite', 'em']:
        style['font-style'] = 'oblique'
    elif tag.name == 'code':
        style['font-family'] = 'courier'
    elif tag.name == 'small':
        style['font-family'] = '0.8em'

