from io import BytesIO

from pdfme import span
from pdfme.standard_fonts import fonts
from pdfme import PDFBase
from pdfme.utils import subs, ref


fonts = {
    '/F1': fonts['helvetica'],
    '/F1B': fonts['helveticaB'],
    '/F1I': fonts['helveticaI'],
    '/F1BI': fonts['helveticaBI'],
}

state = {
    'width': 200,
    'height': 300,
    'fonts': fonts,
    'line-height': 1.1,
    'text-align': 'l',
    'stream': ''
}

contents = [
    'me gusta estar al lado del camino mirando el humo mientras todo pasa ',
    {'style': {'font': ['/F1', 12]}, 'content': [
        'me gusta abrir los ojos y estar vivo tener que vermelas con la resaca ',
        {'style': {'font': ['/F1BI', 12]}, 'content': [
            'entonces navegar se hace preciso'
        ]},
            ' en barcos que se estrellan en la nada, vivir atormentado es sentido',
    ]},
    ' creo que esta si es la parte mas pesada ',
    {'style': {'color': [1,0.3,0.7]}, 'content': [
        'en tiempos donde nadie escucha a nadie'
    ]},
    ' en tiempos donde',
    {'style': {'sub': 1.2}, 'content': ['todos']},
    ' contra ',
    {'style': {'sup': 1.2}, 'content': ['todos']},
    ' en tiempos egoístas y ',
    {'style': {'font': ['/F1B', 16]}, 'content': ['mezquinos']},
    ' en tiempos donde siempre estamos solos'
]

rest = span.inline_tag(contents, {'font': ['/F1', 12]}, state)

pdf = PDFBase()
root, _ = pdf.add({ 'Type': b'/Catalog'})
pdf.trailer['Root'] = ref(root)
content, _ = pdf.add({ '__stream__': subs('BT 1 0 0 1 60 500 Tm{} ET', state['stream']) })
pages, _ = pdf.add({ 'Type': b'/Pages', 'Kids': [], 'Count': 1 })
pdf[1]['Pages'] = ref(pages)

fonts_= {}
fonts_ex = (('F1', 'Helvetica'), ('F1B', 'Helvetica-Bold'), 
    ('F1I', 'Helvetica-Oblique'), ('F1BI', 'Helvetica-BoldOblique'))
for name, font_name in fonts_ex:
    i, _ = pdf.add({
        'Type': b'/Font',
        'Subtype': b'/Type1',
        'BaseFont': subs('/{}', font_name),
        'Encoding': b'/WinAnsiEncoding'
    })
    fonts_[name] = ref(i)


page,_ = pdf.add({
    'Type': b'/Page',
    'Parent': ref(pages),
    'MediaBox': [0, 0, 612, 792],
    'Resources': {
        'ProcSet': [b'/PDF',b'/Text'],
        'Font': fonts_
    },
    'Contents': ref(content)
})

pdf[pages]['Kids'].append(ref(page))

with open('test.pdf', 'wb') as f:
    pdf.output(f)
