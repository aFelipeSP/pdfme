
from pdfme import PDF
from pdfme.graphics import create_graphics_from_dicts


def test_graphics():
    pdf_graphics = create_graphics_from_dicts([
        dict(type='line', x1=10, y1=10, x2=50, y2=50, stroke='brown'),
        dict(type='ellipse', cx=200, cy=200, rx=40, ry=40),
        dict(type='ellipse', cx=200, cy=200, rx=20, ry=70),
        dict(type='rect', x=100, y=100, height=20, width=40),
        dict(type='ellipse', cx=50, cy=300, rx=40, ry=40, fill='red'),
        dict(type='ellipse', cx=100, cy=70, rx=70, ry=20, fill='yellow'),
        dict(type='rect', x=200, y=200, height=20, width=40, fill='blue'),
        dict(type='ellipse', cx=400, cy=200, rx=70, ry=30, fill='yellow', stroke=None),
        dict(type='rect', x=200, y=700, height=20, width=40, fill='blue', stroke=None),
        dict(type='rect', x=200, y=400, height=100, width=200, fill='darkblue', border_radius=20, line_width=10, box_sizing='content'),
        dict(type='rect', x=200, y=300, height=100, width=200, fill='darkred', border_radius=20, stroke=None),
        dict(type='ellipse', cx=250, cy=550, rx=50, ry=50, fill='red', line_width=10),
        dict(type='ellipse', cx=350, cy=550, rx=50, ry=50, fill='red', stroke=None),
        dict(type='path', fill='red', stroke=None, path='300 40 m 350 40 l 360 40 370 50 370 60 c h'),
        dict(type='path', fill='blue', line_width=10, line_join='bevel', path='400 40 m 450 40 l 460 40 470 50 470 60 c h'),
        dict(type='ellipse', cx=50, cy=50, rx=50, ry=50, fill='blue', line_width=10),
    ])

    pdf = PDF()
    pdf.add_page()
    print(pdf_graphics.width, pdf_graphics.height)
    stream = pdf_graphics.result
    pdf.page.add('q 1 0 0 1 0 0 cm {} Q'.format(stream))

    with open('test_graphics.pdf', 'wb') as f:
        pdf.output(f)

