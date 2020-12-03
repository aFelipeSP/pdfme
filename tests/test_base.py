from pdfme import PDF
import random
import json

abc = 'abcdefghijklmnñopqrstuvwxyzáéíóú'

def gen_word():
    return ''.join(random.choice(abc) for _ in range(random.randint(1, 10)))

def gen_text(n):
    return ' '.join(gen_word() for _ in range(n))

def gen_struct(n, m=4):

    attr = random.choice(['b','i','n'])
    obj = {attr: [], 'style': {}}

    styles = {
        'font_family': ['Helvetica', 'Times', 'Courier'],
        'font_size': list(range(9, 17)),
        'font_weight': ['normal', 'bold'],
        'font_style': ['normal', 'oblique'],
        'color': [[round(random.random(),3) for _ in range(3)]]
    }

    if m == 0:
        obj[attr].append(gen_text(random.randint(5, 20)))
        return obj

    for style, opts in styles.items():
        obj['style'][style] = random.choice(opts)

    i = 0
    while i < n:
        if i%2 != 0:
            obj[attr].append(gen_struct(max(round(n/2), 1), m-1))
        else:
            obj[attr].append(gen_text(random.randint(5, 20)))
        i += 1

    return obj

t = 0

if t:
    struct = gen_struct(9)
    style = struct.pop('style')
    content = struct[list(struct.keys())[0]]
    with open('borrar.json', 'w') as f:
        json.dump(content, f, indent=4, ensure_ascii=False)
else:
    with open('borrar.json') as f:
        content = json.load(f)

pdf = PDF()

pdf.stream('0.9 0.9 0.9 rg {} {} {} {} re F'.format(pdf.margins[3], pdf.margins[2],pdf.width,pdf.height))

ret = pdf.text(content, text_align='j')

while not ret is None:
    pdf.add_page()
    ret = pdf.text(ret, text_align='j')

with open('test.pdf', 'wb') as f:
    pdf.output(f)
