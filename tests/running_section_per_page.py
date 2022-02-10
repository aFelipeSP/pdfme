from pdfme import build_pdf

from .utils import gen_text

def test_running_section_per_page():
    document = {
        "running_sections": {
            "header": {
                "x": "left", "y": 20, "height": "top", "style": {"text_align": "r"},
                "content": [{".b": "This is a header"}],
                "include": "0,4:40:2",
                "exclude": "2"
            }
        },
        "sections": [
            {
                "content": [gen_text(100) for _ in range(50)]
            },
        ]
    }

    with open('test_running_section_per_page.pdf', 'wb') as f:
        build_pdf(document, f)
   