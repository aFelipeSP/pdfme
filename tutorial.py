from pdfme import build_pdf
from pathlib import Path
import tempfile

image_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xf9\xfe\x8a(\xa0\x0f\xff\xd9'

image_path = Path(tempfile.gettempdir()) / 'temp_image.jpg'
with image_path.open('wb') as g:
    g.write(image_bytes) 

document = {}

document['style'] = {
    'margin_bottom': 15,
    'text_align': 'j'
}

document['formats'] = {
    'url': {'c': 'blue', 'u': 1},
    'title': {'b': 1, 's': 13}
}

document['running_sections'] = {
    'header': {
        'x': 'left', 'y': 20, 'height': 'top',
        'style': {'text_align': 'r'},
        'content': [{'.b': 'This is a header'}],
        'include': '0:4:2'
    },
    'footer': {
        'x': 'left', 'y': 800, 'height': 'bottom',
        'style': {'text_align': 'c'},
        'content': [{'.': ['Page ', {'var': '$page'}]}]
    }
}

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
    'image': str(image_path),
    'style': {'margin_left': 100, 'margin_right': 100}
})

content1.append({
    "style": {"margin_left": 160, "margin_right": 160},
    "group": [
        {"image": str(image_path)},
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
