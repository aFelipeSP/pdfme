from pdfme import build_pdf

from .utils import gen_text

def test_group_element():
    document = {
        "sections": [{"content": [
            *[gen_text(100) for _ in range(4)],
            {"style": {"margin_left": 80, "margin_right": 80}, "group": [
                {"image": "tests/image_test.jpg"},
                gen_text(50)
            ]}
        ]}]
    }

    with open('test_group_element.pdf', 'wb') as f:
        build_pdf(document, f)
