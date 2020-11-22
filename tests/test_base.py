from io import BytesIO

from pdfme import PDFBase
from pdfme.utils import subs, ref

pdf = PDFBase({
    'Type': b'/Catalog',
    'Pages': None
})

font = pdf.add({
    'Type': b'/Font',
    'Subtype': b'/Type1',
    'Name': b'/F1',
    'BaseFont': b'/Helvetica'
})

content = pdf.add({
    'Filter': b'/FlateDecode',
    '__stream__': b'BT\n/F1 24 Tf\n1 0 0 1 260 600 Tm\n(Hello World)Tj\nET'
})

pages = pdf.add({
    'Type': b'/Pages',
    'Kids': [],
    'Count': 1
})

pdf[1]['Pages'] = ref(pages)

page = pdf.add({
    'Type': b'/Page',
    'Parent': ref(pages),
    'MediaBox': [0, 0, 612, 792],
    'Resources': {
        'ProcSet': [b'/PDF',b'/Text'],
        'Font': {
            'F1': ref(font)
        }
    },
    'Contents': ref(content)
})

pdf[pages]['Kids'].append(ref(page))

with open('test.pdf', 'wb') as f:
    pdf.output(f)

# f = BytesIO()
# pdf.output(f)

# ff = f.getvalue().decode()
for el in pdf:
    print(el)
import pdb; pdb.set_trace()