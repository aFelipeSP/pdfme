from pdfme import build_pdf

from .utils import gen_text

def test_group_element():
    document = {
        "sections": [{"content": [
            *[gen_text(50) for _ in range(4)],
            {
                "style": {
                    "margin_left": 80,
                    "margin_right": 80,
                    # "shrink": 1
                },
                "group": [
                    {
                        "image": "tests/image_test.jpg",
                        "style": {
                            # "min_height": 50
                        }
                    },
                    gen_text(50),
                    # {"image": "tests/image_test.jpg", "style": {"min_height": 100}},
                ]
            }
        ]}]
    }

    with open('test_group_element.pdf', 'wb') as f:
        build_pdf(document, f)
