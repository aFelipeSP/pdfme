import random
import json
from pdfme import PDF

abc = 'abcdefghijklmnñopqrstuvwxyzáéíóú'

def gen_word():
    return ''.join(random.choice(abc) for _ in range(random.randint(1, 10)))

def gen_text(n):
    return random.choice(['',' ']) + (' '.join(gen_word() for _ in range(n))) + random.choice(['',' '])

def maybe(n=0.5):
    return random.choices([True, False], [n, 1 - n])[0]

def random_color():
    return [round(random.random(), 3) for _ in range(3)]

def gen_rich_text(n):

    style_ = {'b': 1, 'i': 1, 's': random.randint(9, 17), 'c': random_color(),
        'f': random.choice(['Helvetica', 'Times', 'Courier']),
        'u': 1,
        'bg': random_color(),
        'r': random.choice([-0.4, 0.4] + [0]*10),
    }

    obj = {}
    key = '.'

    if maybe(): obj['style'] = {k:v for k, v in style_.items() if maybe()}
    else:
        style = []
        for k, v in style_.items():
            if maybe():
                if k in ['b', 'i', 'u']: style.append(k)
                elif k == 'r' and v != 0: style.append(k+':'+str(v))
                elif k in ['bg', 'c']: style.append(k+':'+ (' '.join(str(t) for t in v)))
                else: style.append(k+':'+str(v))
        key += ';'.join(style)

    obj[key] = []
    i = 1
    while n > 0:
        words = min(int(n/3), random.randint(1, 40))
        if words == 0: break
        n -= words
        if i%2 == 0 and words > 1:
            ans = gen_rich_text(words)
            if ans is not None:
                obj[key].append(ans)
        else:
            if len(obj[key]) and isinstance(obj[key][-1], str): obj[key][-1] += gen_text(words)
            else: obj[key].append(gen_text(words))
        i += 1

    return obj

def gen_content(size, level=1):

    style = {}
    if maybe(0.1): style['b'] = 1
    if maybe(0.1): style['i'] = 1
    if maybe(0.1): style['u'] = 1
    if maybe(0.1): style['c'] = random_color()
    if maybe(0.1):
        style['f'] = random.choices(['Helvetica', 'Times', 'Courier'], [8, 1, 1])[0]
    if maybe(0.1): style['bg'] = random_color()
    if level == 1 or maybe(0.1):
        style['s'] = random.triangular(4, (0.15 * (1 - level) + 1) * 8, 5)
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
    obj = {'style': style, 'content': c, 'cols': {"count": random.randint(2,3)}}
    n = int(random.triangular(3, (0.15 * (1 - level) + 1) * size))
    l = random.choice([0,1])

    if level == 3:
        c.append(gen_text(random.randint(50, 300)))
        return obj

    for i in range(n):
        if i%2 == l:
            ans = gen_content(size, level + 1)
            c.append(ans)
        else:
            if maybe(0.5):
                c.append(gen_text(random.randint(50, 300)))
            else:
                c.append({'image': 'tests/image_test.jpg', 'style': 
                    {'image_place': 'flow' if maybe(0.7) else 'normal'}
                })

    return obj
