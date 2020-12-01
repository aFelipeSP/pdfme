from pdfme import PDF
import random

abc = 'abcdefghijklmnñopqrstuvwxyzáéíóú'

def gen_word():
    return ''.join(random.choice(abc) for _ in range(random.randint(1, 10)))

def gen_text(n):
    return ' '.join(gen_word() for _ in range(n))

pdf = PDF()
pdf.text(gen_text(1000), text_align='j')

with open('test.pdf', 'wb') as f:
    pdf.output(f)
