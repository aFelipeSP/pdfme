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

