from pdfme import build_pdf
from pdfme.fonts import PDFFont

PDFFont.register('Open Sans', 'n', './fonts/OpenSans-Regular.ttf')
PDFFont.register('Open Sans', 'b', './fonts/OpenSans-Bold.ttf')

document = {}

document['style'] = {
    'margin_bottom': 15,
    'text_align': 'j',
    'f': 'Open Sans'
}

document['formats'] = {
    'url': {'c': 'blue', 'u': 1},
    'title': {'b': 1, 's': 13}
}

document['running_sections'] = {
    'header': {
        'x': 'left', 'y': 20, 'height': 'top',
        'style': {'text_align': 'r'},
        'content': [{'.b': 'This is a header'}]
    },
    'footer': {
        'x': 'left', 'y': 800, 'height': 'bottom',
        'style': {'text_align': 'c'},
        'content': [{'.': ['Page ', {'var': '$page'}]}]
    }
}

document['per_page'] = [
    {'pages': '1:1000:2', 'style': {'margin': [60, 100, 60, 60]}},
    {'pages': '0:1000:2', 'style': {'margin': [60, 60, 60, 100]}},
    {'pages': '0:4:2', 'running_sections': {'include': ['header']}},
]

document['sections'] = []
section1 = {}
document['sections'].append(section1)

section1['style'] = {
    'page_numbering_style': 'roman'
}

section1['running_sections'] = ['footer']

section1['content'] = content1 = []

content1.append({
    '.': 'A Title', 'style': 'title', 'label': 'title1',
    'outline': {'level': 1, 'text': 'A different title 1'}
})

content1.append(
    ['This is a paragraph with a ', {'.b;c:green': 'bold green part'}, ', a ',
    {'.': 'link', 'style': 'url', 'uri': 'https://some.url.com'},
    ', a footnote', {'footnote': 'description of the footnote'},
    ' and a reference to ',
    {'.': 'Title 2.', 'style': 'url', 'ref': 'title2'}]
)

content1.append({
    'image': "tests/image_test.jpg",
    'style': {'margin_left': 100, 'margin_right': 100}
})

content1.append({
    "style": {"margin_left": 160, "margin_right": 160},
    "group": [
        {"image": "tests/image_test.png"},
        {".": "Figure 1: Description of figure 1"}
    ]
})

table_def1 = {
    'widths': [1.5, 1, 1, 1],
    'style': {'border_width': 0, 'margin_left': 70, 'margin_right': 70},
    'fills': [{'pos': '1::2;:', 'color': 0.7}],
    'borders': [{'pos': 'h0,1,-1;:', 'width': 0.5}],
    'table': [
        ['', 'column 1', 'column 2', 'column 3'],
        ['count', '2000', '2000', '2000'],
        ['mean', '28.58', '2643.66', '539.41'],
        ['std', '12.58', '2179.94', '421.49'],
        ['min', '1.00', '2.00', '1.00'],
        ['25%', '18.00', '1462.00', '297.00'],
        ['50%', '29.00', '2127.00', '434.00'],
        ['75%', '37.00', '3151.25', '648.25'],
        ['max', '52.00', '37937.00', '6445.00']
    ]
}

content1.append(table_def1)

table_def2 = {
    'widths': [1.2, .8, 1, 1],
    'table': [
        [
            {
                'colspan': 4,
                'style': {
                    'cell_fill': [0.8, 0.53, 0.3],
                    'text_align': 'c'
                },
                '.b;c:1;s:12': 'Fake Form'
            },None, None, None
        ],
        [
            {'colspan': 2, '.': [{'.b': 'First Name\n'}, 'Fakechael']}, None,
            {'colspan': 2, '.': [{'.b': 'Last Name\n'}, 'Fakinson Faker']}, None
        ],
        [
            [{'.b': 'Email\n'}, 'fakeuser@fakemail.com'],
            [{'.b': 'Age\n'}, '35'],
            [{'.b': 'City of Residence\n'}, 'Fake City'],
            [{'.b': 'Cell Number\n'}, '33333333333'],
        ]
    ]
}

content1.append(table_def2)

document['sections'].append({
    'style': {
        'page_numbering_reset': True, 'page_numbering_style': 'arabic'
    },
    'running_sections': ['footer'],
    'content': [

        {
            '.': 'Title 2', 'style': 'title', 'label': 'title2',
            'outline': {}
        },

        {
            'style': {'list_text': '1.  '},
            '.': ['This is a list paragraph with a reference to ',
            {'.': 'Title 1.', 'style': 'url', 'ref': 'title1'}]
        }
    ]
})

with open('test_tutorial.pdf', 'wb') as f:
    build_pdf(document, f)
