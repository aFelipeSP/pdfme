import json
from pathlib import Path

from .utils import gen_rich_text
from pdfme import PDF

def page_rect(pdf):
    pdf.page.add('q 0.9 g {} {} {} {} re F Q'.format(
        pdf.margin['left'], pdf.margin['bottom'],
        pdf.page.content_width, pdf.page.content_height
    ))

def output(pdf, name):
    with open(name, 'wb') as f:
        pdf.output(f)

def add_content(content, text_options, name):
    pdf = PDF()
    pdf.add_page()
    page_rect(pdf)
    pdf_text = pdf._text(
        content, x=pdf.page.margin_left, width=pdf.page.content_width,
        **text_options
    )
    while not pdf_text.finished:
        pdf.add_page()
        page_rect(pdf)
        pdf_text = pdf._text(pdf_text)
    output(pdf, name + '.pdf')


def base(text_options={}, name='test', words=5000):
    input_file = Path(name + '.json')
    if input_file.exists():
        with input_file.open(encoding='utf8') as f:
            content = json.load(f)
    else:
        content = gen_rich_text(words)
        with input_file.open('w', encoding='utf8') as f:
            json.dump(content, f, ensure_ascii=False)
    add_content(content, text_options, name)

def test_text_indent():
    base({'indent': 20, 'text_align': 'j'}, 'test_text_indent')

def test_text_line_height():
    base({'line_height': 2}, 'test_text_line_height')

def test_text_left():
    base({}, 'test_text')

def test_text_right():
    base({'text_align': 'r'}, 'test_text_right')

def test_text_center():
    base({'text_align': 'c'}, 'test_text_center')

def test_text_justify():
    base({'text_align': 'j'}, 'test_text_justify')

def test_text_list():
    base({'list_text': '1. '}, 'test_text_list', 500)

def test_text_list_style():
    base({'list_text': chr(183) + ' ', 'list_style': {'f': 'Symbol'}}, 
        'test_text_list_style', 500)

def test_text_list_style_indent():
    base(
        {
            'list_text': chr(183) + ' ', 'list_style': {'f': 'Symbol'},
            'list_indent': 40, 'indent': 20
        },
        'test_text_list_style_indent', 500
    )

def get_content_list(content):
    for key, val in content.items():
        if key.startswith('.'):
            return val

def append_text(content, new):
    for key, val in content.items():
        if key.startswith('.'):
            val.extend(new)
            break

def test_text_ref_label():
    content = gen_rich_text(1)
    append_text(content, [{'ref': 'asdf', '.': 'asd fa sdf asdf asdfa sdfa'}])
    append_text(content, get_content_list(gen_rich_text(500)))
    append_text(content, [{'label': 'asdf', '.': 'ertyer sdfgsd'}])
    append_text(content, get_content_list(gen_rich_text(1000)))
    add_content(content, {}, 'test_text_ref_label')

def test_text_link():
    content = gen_rich_text(500)
    append_text(content, [{'uri': 'www.google.com', '.': 'its me google '*10}])
    append_text(content, get_content_list(gen_rich_text(1000)))
    append_text(content, [{'uri': 'www.google.com', '.': 'its me google '*10}])
    append_text(content, get_content_list(gen_rich_text(500)))
    add_content(content, {}, 'test_text_link')