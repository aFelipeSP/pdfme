import json
from pathlib import Path

from .utils import gen_rich_text
from pdfme import PDF

def page_rect(pdf):
    rect = 'q 0.9 0.9 0.9 rg {} {} {} {} re F Q'.format(
        pdf.margin['left'], pdf.margin['bottom'], pdf.width, pdf.height
    )
    pdf.page.add(rect)
    return rect

def output(pdf, name):
    with open(name, 'wb') as f:
        pdf.output(f)

def base(text_options={}, name='test', words=5000):
    input_file = Path(name + '.json')
    if input_file.exists():
        with input_file.open() as f:
            content = json.load(f)
    else:
        content = gen_rich_text(words)
        with input_file.open('w') as f:
            json.dump(content, f, ensure_ascii=False)
    pdf = PDF()
    pdf.add_page()
    page_rect(pdf)
    pdf.text(content, **text_options)
    output(pdf, name + '.pdf')

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
    base({'list_text': chr(183) + ' ', 'list_style': {'f': 'Symbol'}, 'list_indent': 40}, 
        'test_text_list_style_indent', 500)

def test_text_ref_label():
    pdf = PDF()
    pdf.add_page()
    page_rect(pdf)
    pdf.text({'ref': 'asdf', '.': 'asd fa sdf asdf asdfa sdfa'})
    pdf.text(gen_rich_text(1000))
    pdf.text({'label': 'asdf', '.': 'ertyer sdfgsd'})
    pdf.text(gen_rich_text(1000))
    output(pdf, 'test_text_ref_label.pdf')
