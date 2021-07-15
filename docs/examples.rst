Examples
========

Example of a PDF document created with :func:`pdfme.document.build_pdf` using
almost all of the functionalities of this library. 
   
.. code-block::

    import random

    from pdfme import build_pdf


    random.seed(1)
    abc = 'abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZáéíóúÁÉÍÓÚ'

    def gen_word():
        return ''.join(random.choice(abc) for _ in range(random.randint(1, 10)))

    def gen_text(n):
        return random.choice(['',' ']) + (' '.join(gen_word() for _ in range(n))) + random.choice(['',' '])

    def gen_paragraphs(n):
        return [gen_text(random.randint(50, 200)) for _ in range(n)]

    document = {
        "style": {"margin_bottom": 15, "text_align": "j"},
        "formats": {
            "url": {"c": "blue", "u": 1},
            "title": {"b": 1, "s": 13}
        },
        "running_sections": {
            "header": {
                "x": "left", "y": 20, "height": "top", "style": {"text_align": "r"},
                "content": [{".b": "This is a header"}]
            },
            "footer": {
                "x": "left", "y": 740, "height": "bottom", "style": {"text_align": "c"},
                "content": [{".": ["Page ", {"var": "$page"}]}]
            }
        },
        "page_style": {
            "page_size": "letter",
            "margin": [60, 50]
        },
        "sections": [
            {
                "page_style": {"page_numbering_style": "roman"},
                "running_sections": ["footer"],
                "content": [

                    {".": "A Title", "style": "title", "label": "title1"},

                    ["This is a paragraph with a ", {".b": "bold part"}, ", a ",
                    {".": "link", "style": "url", "uri": "https://some.url.com"},
                    ", a footnote", {"footnote": "description of the footnote"},
                    " and a reference to ",
                    {".": "Title 2.", "style": "url", "ref": "title2"}],

                    *gen_paragraphs(7),

                    {
                        "widths": [1.5, 2.5, 1, 1.5, 1, 1],
                        "style": {"s": 9},
                        "table": [
                            [
                                gen_text(4),
                                {
                                    "colspan": 5,
                                    "style": {
                                        "cell_fill": [0.57, 0.8, 0.3],
                                        "text_align": "c", "cell_margin_top": 13
                                    },
                                    ".b;c:1;s:12": gen_text(4)
                                },None, None, None, None
                            ],
                            [
                                {"colspan": 2, ".": [{".b": gen_text(3)}, gen_text(3)]}, None,
                                {".": [{".b": gen_text(1) + "\n"}, gen_text(3)]},
                                {".": [{".b": gen_text(1) + "\n"}, gen_text(3)]},
                                {".": [{".b": gen_text(1) + "\n"}, gen_text(3)]},
                                {".": [{".b": gen_text(1) + "\n"}, gen_text(3)]}
                            ],
                            [
                                {
                                    "colspan": 6, "cols": {"count": 3, "gap": 20},
                                    "style": {"s": 8},
                                    "content": gen_paragraphs(10)
                                },
                                None, None, None, None, None
                            ]
                        ]
                    },

                    *gen_paragraphs(10),
                ]
            },
            {
                "page_style": {
                    "page_numbering_reset": True, "page_numbering_style": "arabic"
                },
                "running_sections": ["header", "footer"],
                "content": [

                    {".": "Title 2", "style": "title", "label": "title2"},

                    ["This is a paragraph with a reference to ",
                    {".": "Title 1.", "style": "url", "ref": "title1"}],

                    {
                        "style": {"list_text": "1.  "},
                        ".": "And this is a list paragraph." + gen_text(40)
                    },

                    *gen_paragraphs(10)
                ]
            },
        ]
    }

    with open('document.pdf', 'wb') as f:
        build_pdf(document, f)

