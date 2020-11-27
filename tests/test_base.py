from pdfme import span
from pdfme.standard_fonts import fonts


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
    {'style': {'font': ['helveticaB', 12]}, 'content': [
        'me gusta abrir los ojos y estar vivo tener que vermelas con la resaca ',
        {'style': {'font': ['helveticaBI', 12]}, 'content': [
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
    {'style': {'font': ['helveticaB', 16]}, 'content': ['mezquinos']},
    ' en tiempos donde siempre estamos solos'
]

rest = span.inline_tag(contents, {'font': ['helvetica', 12]}, state)

print(state['stream'])
