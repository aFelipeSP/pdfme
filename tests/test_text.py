from .utils import gen_rich_text
from pdfme import PDF

def page_rect(pdf):
    rect = '0.9 0.9 0.9 rg {} {} {} {} re F'.format(pdf.margin['left'], pdf.margin['bottom'], pdf.width,pdf.height)
    pdf.stream(rect)
    return rect

def output(pdf, pdf_name):
    with open(pdf_name, 'wb') as f:
        pdf.output(f)

def add_remaining(pdf, ret, rect=None, text_options={}):
    while not ret is None:
        pdf.add_page()
        if rect is not None: pdf.stream(rect)
        ret = pdf.text(ret, **text_options)

def base(text_options={}, pdf_name='test.pdf', words=5000):
    content = gen_rich_text(words)
    pdf = PDF()
    rect = page_rect(pdf)
    ret = pdf.text(content, **text_options)
    add_remaining(pdf, ret, rect, text_options)
    output(pdf, pdf_name)

def test_text_indent():
    base({'indent': 20, 'text_align': 'j'}, 'test_text_indent.pdf')

def test_text_line_height():
    base({'line_height': 2}, 'test_text_line_height.pdf')

def test_text_left():
    base({}, 'test_text.pdf')

def test_text_right():
    base({'text_align': 'r'}, 'test_text_right.pdf')

def test_text_center():
    base({'text_align': 'c'}, 'test_text_center.pdf')

def test_text_justify():
    base({'text_align': 'j'}, 'test_text_justify.pdf')

def test_text_list():
    base({'list_text': '1. '}, 'test_text_list.pdf', 500)

def test_text_list_style():
    base({'list_text': chr(183) + ' ', 'list_style': {'f': 'Symbol'}}, 
        'test_text_list_style.pdf', 500)

def test_text_list_style_indent():
    base({'list_text': chr(183) + ' ', 'list_style': {'f': 'Symbol'}, 'list_indent': 40}, 
        'test_text_list_style_indent.pdf', 500)

def test_text_ref_label():
    pdf = PDF()
    rect = page_rect(pdf)
    pdf.text({'ref': 'asdf', '.': 'asd fa sdf asdf asdfa sdfa'})
    ret = pdf.text(gen_rich_text(1000))
    add_remaining(pdf, ret, rect)
    pdf.text({'label': 'asdf', '.': 'ertyer sdfgsd'})
    ret = pdf.text(gen_rich_text(1000))
    add_remaining(pdf, ret, rect)
    output(pdf, 'test_text_ref_label.pdf')
