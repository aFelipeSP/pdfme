from pdfme import PDF
import json

from .utils import gen_rich_text, maybe, gen_text, gen_content

def test_content():
    for i in range(6):
        pdf = PDF()
        struct = gen_content()
        pdf.add_content(struct)
        with open('test_content{}.pdf'.format(i), 'wb') as f:
            pdf.output(f)

        with open('test_content{}.json'.format(i), 'w') as f:
            json.dump(struct, f)