from pdfme import PDF
import random
import json

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
        return {'s': style, 'c': gen_text(random.randint(5, 20))}

    obj = {'s': style, 'c': []}

    i = 1
    while i < n:
        if i%2 == 0:
            obj['c'].append(gen_struct(max(round(n/2), 1), m-1))
        else:
            obj['c'].append(gen_text(random.randint(5, 20)))
        i += 1

    return obj

t = 2
if t == 1:
    content = gen_struct(11)
    with open('borrar.json', 'w') as f:
        json.dump(content, f)
elif t == 0:
    with open('borrar.json', 'r') as f:
        content = json.load(f)
else:
    content = ['asdfa asdfg h pwer twg er t wertwsdf gs df gs dfgsdferw er tw er tert cllbksdf r', {'s':'u;bg:0.8', 'c':[' asd fa sdf g tg hfgk', {'s':'r:-0.5', 'c':' dzsr aj fg uys'}]}, ' asdfas df asdf asdf a dsf ads fg asdfgt']

print(content)

pdf = PDF()
rect = '0.9 0.9 0.9 rg {} {} {} {} re F'.format(pdf.margins[3], pdf.margins[2],pdf.width,pdf.height)
pdf.stream(rect)
# pdf.image('puppy.jpg')
ret = pdf.text(content, text_align='j')

while not ret is None:
    pdf.add_page()
    pdf.stream(rect)
    ret = pdf.text(ret, text_align='j')

with open('test.pdf', 'wb') as f:
    pdf.output(f)
