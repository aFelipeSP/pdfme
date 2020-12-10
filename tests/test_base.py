from pdfme import PDF
import random
import pickle

abc = 'abcdefghijklmnñopqrstuvwxyzáéíóú'

def gen_word():
    return ''.join(random.choice(abc) for _ in range(random.randint(1, 10)))

def gen_text(n):
    return ' '.join(gen_word() for _ in range(n))

def gen_struct(n, m=4):
    style_ = {
        'f': random.choice(['Helvetica', 'Times', 'Courier']),
        's': random.randint(9, 17),
        'b': random.choice([0,1]),
        'i': random.choice([0,1]),
        'c': [round(random.random(),3) for _ in range(3)]
    }

    if random.choice([0,1]):
        style = {k:v for k, v in style_.items() if random.choice([0,1])}
    else:
        style = []
        for k, v in style_.items():
            attr = ''
            if random.choice([0,1]):
                if k in ['b', 'i'] and v == 0: continue
                attr += k
                if k in ['b', 'i'] and v == 1: continue
                if k == 'c': v = ' '.join(str(t) for t in v)
                attr += ':' + str(v)
                style.append(attr)
        style = ';'.join(style)

    if m == 0:
        return (style, gen_text(random.randint(5, 20)))

    obj = (style, [])

    i = 1
    while i < n:
        if i%2 == 0:
            obj[1].append(gen_struct(max(round(n/2), 1), m-1))
        else:
            obj[1].append(gen_text(random.randint(5, 20)))
        i += 1

    return obj

t = 1
from fpdf import FPDF
if t:
    content = gen_struct(11)
    with open('borrar.pk', 'wb') as f:
        pickle.dump(content, f)
else:
    with open('borrar.pk', 'rb') as f:
        content = pickle.load(f)

# print(content)

pdf = PDF()
rect = '0.9 0.9 0.9 rg {} {} {} {} re F'.format(pdf.margins[3], pdf.margins[2],pdf.width,pdf.height)
pdf.image('puppy.jpg')
pdf.stream(rect)
ret = pdf.text(content, text_align='j')

while not ret is None:
    pdf.add_page()
    pdf.stream(rect)
    ret = pdf.text(ret, text_align='j')

with open('test.pdf', 'wb') as f:
    pdf.output(f)
