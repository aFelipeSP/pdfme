import random

abc = 'abcdefghijklmnñopqrstuvwxyzáéíóú'

def gen_word():
    return ''.join(random.choice(abc) for _ in range(random.randint(1, 10)))

def gen_text(n):
    return random.choice(['',' ']) + (' '.join(gen_word() for _ in range(n))) + random.choice(['',' '])

def maybe():
    return random.choice([0,1])

def random_color():
    return [round(random.random(), 3) for _ in range(3)]

def gen_rich_text(n):

    style_ = {'b': 1, 'i': 1, 's': random.randint(9, 17), 'c': random_color(),
        'f': random.choice(['Helvetica', 'Times', 'Courier']),
        # 'u': 1,
        # 'bg': random_color(),
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

def gen_content(level=1):

    style = {
        'b': random.choices([1, 0], [1, 9])[0],
        'i': random.choices([1, 0], [1, 9])[0],
        's': random.triangular(5, (0.15 * (1 - level) + 1) * 10, 6),
        'c': random.choices([random_color(), None], [1, 9])[0],
        'f': random.choices(['Helvetica', 'Times', 'Courier'], [8, 1, 1])[0],
        'u': random.choices([1, 0], [1, 9])[0],
        'bg': random.choices([random_color(), None], [1, 9])[0],
        'r': random.choices([random.triangular(-0.4, 0.4), 0], [1, 9])[0],
        'text_align': random.choices(['j', 'c', 'l', 'r'], [5, 1, 2, 2])[0],
        'line_height': random.triangular(1, 1.5),
        'indent': random.triangular(0, 20, 0)
    }

    c = []
    obj = {'style': style, 'content': c, 'cols': {"count": random.randint(2,3)}}
    n = random.randint(5, 10)
    l = random.choice([0,1])

    if level == 3:
        c.append(gen_text(random.randint(100, 500)))
        return obj

    for i in range(n):
        if i%2 == l:
            ans = gen_content(level + 1)
            c.append(ans)
        else:
            c.append(gen_text(random.randint(100, 500)))

    return obj