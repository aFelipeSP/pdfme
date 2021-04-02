import random

abc = 'abcdefghijklmnñopqrstuvwxyzáéíóú'

def gen_word():
    return ''.join(random.choice(abc) for _ in range(random.randint(1, 10)))

def gen_text(n):
    return ' '.join(gen_word() for _ in range(n))

def maybe():
    return random.choice([0,1])

def gen_rich_text(n=500, m=2, ref=None, w=None):

    if m == 0: return

    if ref is None:
        ref = {'n': n}

    if w is None:
        w = n

    if ref['n'] <= 0:
        return

    style_ = {
        'f': random.choice(['Helvetica', 'Times', 'Courier']),
        's': random.randint(9, 17),
        'b': maybe(),
        'i': maybe(),
        # 'u': maybe(),
        # 'bg': [round(random.random(),3) for _ in range(3)],
        'c': [round(random.random(),3) for _ in range(3)],
        'r': random.choice([-0.4, 0.4] + [0]*10),
    }

    if maybe():
        style = {k:v for k, v in style_.items() if maybe()}
    else:
        style = []
        for k, v in style_.items():
            attr = ''
            if maybe():
                if k in ['b', 'i', 'u'] and v == 0: continue
                attr += k
                if k in ['b', 'i', 'u'] and v == 1: continue
                if k == 'c': v = ' '.join(str(t) for t in v)
                if k == 'bg': v = ' '.join(str(t) for t in v)
                attr += ':' + str(v)
                style.append(attr)
        style = ';'.join(style)

    if m == 0:
        words = min(ref['n'], random.randint(1, 5))
        ref['n'] -= words
        return {'s': style, 't': gen_text(words)}

    obj = {'s': style, 't': []}

    i = 1
    while ref['n']:
        words = min(ref['n'], random.randint(1, w))
        ref['n'] -= words
        if i%2 == 0:
            ans = gen_rich_text(m=m-1, ref=ref, w=round(w/4))
            if ans is not None:
                obj['t'].append(ans)
        else:
            obj['t'].append(gen_text(words))
        i += 1

    return obj


def get_char_width(char, size, fonts, font_family, font_mode):
    return size * fonts[font_family][font_mode]['widths'][char] / 1000

def get_word_width(word, size, fonts, font_family, font_mode):
    width = 0
    for char in word:
        width += get_char_size(char, size, fonts, font_family, font_mode)
    return width