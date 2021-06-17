import random
import json
from pdfme import PDF

abc = 'abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZáéíóúÁÉÍÓÚ'

def gen_word():
    return ''.join(random.choice(abc) for _ in range(random.randint(1, 10)))

def gen_text(n):
    return random.choice(['',' ']) + (' '.join(gen_word() for _ in range(n))) + random.choice(['',' '])

def maybe(n=0.5):
    return random.choices([True, False], [n, 1 - n])[0]

def color():
    return [random.uniform(0.5, 1) for _ in range(3)]

def gen_rich_text(n, size=10):

    style_ = {
        'b': 1, 'i': 1, 's': random.triangular(size/2, size, size),
        'f': random.choices(['Helvetica', 'Times', 'Courier'], [3, 1, 1])[0],
        'c': color(), 'bg': color(), 'r': random.triangular(-0.4, 0.4), 'u': 1
    }

    obj = {}
    key = '.'

    if maybe():
        obj['style'] = {k:v for k, v in style_.items() if maybe(.1)}
    else:
        style = []
        for k, v in style_.items():
            if maybe():
                if k in ['b', 'i', 'u']:
                    style.append(k)
                elif k == 'r' and v != 0:
                    style.append(k+':'+str(v))
                elif k in ['bg', 'c']:
                    style.append(k+':'+ (' '.join(str(t) for t in v)))
                else:
                    style.append(k+':'+str(v))
        key += ';'.join(style)

    obj[key] = []
    i = 1
    while n > 0:
        words = min(int(n / 3), random.randint(1, 40))
        if words == 0:
            break
        n -= words
        if i % 2 == 0 and words > 1:
            ans = gen_rich_text(words, size)
            if ans is not None:
                obj[key].append(ans)
        else:
            if len(obj[key]) and isinstance(obj[key][-1], str):
                obj[key][-1] += gen_text(words)
            else:
                obj[key].append(gen_text(words))
        i += 1

    return obj

def gen_content(size, font_size=4, level=1, max_level=3):
    font_size = max(2.5, font_size)
    cols = random.randint(2,3)
    style = {}
    if maybe(0.1): style['b'] = 1
    if maybe(0.1): style['i'] = 1
    if maybe(0.1): style['u'] = 1
    if maybe(0.1): style['c'] = color()
    if maybe(0.1):
        style['f'] = random.choices(['Helvetica', 'Times', 'Courier'], [3, 1, 1])[0]
    if maybe(0.1): style['bg'] = color()
    if level == 1 or maybe(0.1):
        style['s'] = -1.6 * level + font_size + 6 - cols
    if maybe(0.1): style['r'] = random.triangular(-0.4, 0.4)
    if maybe(0.1):
        style['text_align'] = random.choices(['j', 'c', 'l', 'r'], [4, 2, 2, 2])[0]
    if maybe(0.1): style['line_height'] = random.triangular(1, 1.5)
    if maybe(0.1): style['indent'] = random.triangular(0, 20, 0)
    if maybe(0.1): style['margin-left'] = random.triangular(0, 10, 0)
    if maybe(0.1): style['margin-right'] = random.triangular(0, 10, 0)
    if maybe(0.1): style['margin-top'] = random.triangular(0, 10, 0)
    if maybe(0.1): style['margin-bottom'] = random.triangular(0, 10, 0)

    c = []
    obj = {'style': style, 'content': c, 'cols': {"count": cols}}
    n = int(random.triangular(3, (0.15 * (1 - level) + 1) * size))
    l = random.choice([0,1])

    if level == max_level:
        c.append(gen_text(random.randint(50, 300)))
        return obj

    for i in range(n):
        if i%2 == l:
            ans = gen_content(size, font_size, level + 1, max_level)
            c.append(ans)
        else:
            if maybe(0.5):
                c.append(gen_text(random.randint(50, 300)))
            else:
                c.append({'image': 'tests/image_test.jpg', 'style':
                    {'image_place': 'flow' if maybe(0.7) else 'normal'}
                })

    return obj


def gen_table(rows=None, cols=None):
    rows = 20 if rows is None else rows
    cols = int(random.triangular(1, 7, 2)) if cols is None else cols

    obj = {'content': [], 'style': {}}
    obj['widths'] = [random.triangular(3, 6) for _ in range(cols)]
    if maybe(0.1): obj['style']['cell_fill'] = color()
    if maybe(0.1): obj['style']['cell_margin'] = random.triangular(5, 20, 5)
    if maybe(0.1): obj['style']['border_width'] = random.triangular(1, 4)
    if maybe(0.1): obj['style']['border_color'] = color()
    if maybe(0.1): obj['style']['border_style'] = random.choice(['solid', 'dotted', 'dashed'])

    obj['borders'] = [
        {'pos': 'h::2;', 'width': 1.5, 'color': 'green', 'style': 'dotted'},
        {'pos': 'v;1::2', 'width': 2, 'color': 'red', 'style': 'dashed'},
        {'pos': 'h0,1,-1;', 'width': 2.5, 'color': 'blue', 'style': 'solid'},
    ]

    obj['fills'] = [
        {'pos': '::2;::2', 'color': 0.8},
        {'pos': '1::2;::2', 'color': 0.7},
        {'pos': '::2;1::2', 'color': 0.8},
        {'pos': '1::2;1::2', 'color': 0.7},
    ]

    row_spans = {}
    for i in range(rows):
        row = []
        col_spans = 0
        for j in range(cols):
            if col_spans > 0:
                col_spans -= 1
                row.append(None)
            elif row_spans.get(j, {}).get('rows', 0) > 0:
                row_spans[j]['rows'] -= 1
                col_spans = row_spans[j]['cols']
                row.append(None)
            else:
                prob = random.random()
                if prob < 0.2:
                    element = gen_content(1, max_level=2)
                elif prob < 0.7:
                    element = gen_rich_text(200)
                else:
                    element = {'image': 'tests/image_test.jpg', 'style': {
                        'image_place': 'flow' if maybe(0.7) else 'normal'
                    }}
                rowspan = int(random.triangular(1, rows - i, 1))
                colspan = int(random.triangular(1, cols - j, 1))
                col_spans = colspan - 1
                element['rowspan'] = rowspan
                element['colspan'] = colspan
                style = {}
                if maybe(0.1): style['cell_fill'] = color()
                if maybe(0.1): style['cell_margin'] = random.triangular(5, 20, 5)
                element['style'] = style
                row_spans[j] = {'rows': rowspan - 1, 'cols': colspan - 1}
                row.append(element)
        obj['content'].append(row)

    return obj
