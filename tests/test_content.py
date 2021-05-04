from pdfme import PDF
import json

from .utils import gen_rich_text, maybe, gen_text

def test_content():
    dd = [gen_text(500), gen_text(200), gen_text(100), gen_text(500)]
    print(dd)
    struct = {"style": {"margin_bottom": 30, 'text_align': 'j'}, "content": [
        dd[0],
        {"cols": {"count": 2}, "content": [
            dd[1],
            {"cols": {"count": 3}, "content": [
                dd[2]
            ]}
        ]},
        dd[3]
    ]}

    pdf = PDF()
    pdf.add_content(struct)
    with open('test.pdf', 'wb') as f:
        pdf.output(f)
