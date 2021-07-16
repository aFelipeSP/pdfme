Tutorial
========

In this tutorial we will create a PDF document using pdfme to showcase some
of its functionalities.

We will use the preferred way to build a document in pdfme, that is using
:func:`pdfme.document.build_pdf` function. This function receives as its first
argument a nested dict structure with the contents and styling of the document,
and most of this tutorial will be focused in building this dict.

In every step you we will tell you the class or function definition where you
can get more information.

Let's start importing the library and creating the root dictionary where the
definitions that affect the whole document will be stated: ``document``.

.. code-block::

    from pdfme import build_pdf

    document = {}


Now add the ``style`` key to this dictionary, with the styling that all of the
sections will inherit.

.. code-block::

    document['style'] = {
        'margin_bottom': 10,
        'text_align': 'j'
    }


In our example we define the ``margin_bottom`` property, that will be the
default space below every element in the document, and ``text_align`` that will
be the default text alignment for all the paragraphs in the document.
In this dict you can set the default value for the style properties that affect
the paragraphs (``text_align``, ``line_height``, ``indent``, ``list_text``,
``list_style``, ``list_indent``, ``b``, ``i``, ``s``, ``f``, ``u``, ``c``,
``bg``, ``r``), images (``image_flow``), tables (``cell_margin``,
``cell_margin_left``, ``cell_margin_top``, ``cell_margin_right``,
``cell_margin_bottom``, ``cell_fill``, ``border_width``, ``border_color`` and
``border_style``) and content boxes (``margin_top``, ``margin_left``,
``margin_bottom`` and ``margin_right``) inside the document.
For information about paragraph properties see :class:`pdfme.text.PDFText`,
about table properties see :class:`pdfme.table.PDFTable`, and about image and
content properties see :class:`pdfme.content.PDFContent`.

You can set page related properties in ``style`` too like ``page_size``,
``rotate_page``, ``margin``, ``page_numbering_offset`` and
``page_numbering_style`` (see :class:`pdfme.pdf.PDF` definition).

You can also define named style instructions or formats (something like CSS
classes) in ``document`` dict like this:

.. code-block::

    document['formats'] = {
        "url": {"c": "blue", "u": 1},
        "title": {"b": 1, "s": 13}
    }

Every key in ``formats`` dict will be the name of a format that you will be able
to use anywhere in the document. In the example above we define a format for
urls, the typical blue underlined style, and a format for titles with a bigger
font size and bolded text. Given you can use this formats anywhere, the
properties you can add to them are the same you can add to the document's
``style`` we described before.

One more key you can add to ``document`` dict is ``running_sections``. In here
you can define named content boxes that when referenced in a section, will be
added to every page of it. Let's see how we can define a header and footer for
our document using running sections:

.. code-block::

    document['running_sections]: {
        "header": {
            "x": "left", "y": 20, "height": "top",
            "style": {"text_align": "r"},
            "content": [{".b": "This is a header"}]
        },
        "footer": {
            "x": "left", "y": 740, "height": "bottom",
            "style": {"text_align": "c"},
            "content": [{".": ["Page ", {"var": "$page"}]}]
        }
    }

Here we defined running sections ``header`` and ``footer``, with their
respective positions and styles. To know more about running sections see
:class:`pdfme.document.PDFDocument` definition.
We will talk about text formatting later, but one important thing to note here
is the use of ``$page`` variable inside footer's ``content``. This is the way
you can include the number of the page inside a paragraph in pdfme. 

Just defining these running sections won't add them to every page of the
document; you will have to reference them in the section you want to really use
them. Keep reading to see how we add ``header`` and ``footer`` to our sections.

Finally we are going to talk about *sections*. These can have their own page
layout, page numbering, running sections and style, and are the places where we
define the contents of the document. It's important to note that after every
section there's a page break.

Let's create ``sections`` list to contain the documents sections, and add
our first section ``section_1``.

.. code-block::

    document['sections'] = []
    section_1 = {}
    document['sections'].append(section_1)

A section is just a content box, a multi-column element where you can add
paragraphs, images, tables and even content boxes themselves (see 
:class:`pdfme.content.PDFContent` for more informarion about content boxes).
pdfme will put every element from a section in the PDF document from top to 
bottom, and when the first page is full it will add a new page to keep
adding elements to the document, and will keep adding pages until all of the
elements are inside the document.

Like a regular content box you can add a ``style`` to a section, where you can
reference a format from the ``formats`` dict we created before, or a new
``style`` dict, and with this you can override any of the default style
properties of the document.

.. code-block::

    section1['style'] = {
        "page_numbering_style": 'roman'
    }

Here we override only ``page_numbering_style``, a property that sets the style
of the page numbers inside the section (see :class:`pdfme.pdf.PDF` definition).
Default value is ``arabic`` style, and here we change it to ``roman`` (at least
for this section).

Now we are going to reference the running sections that we will use in this
section.

.. code-block::

    section1['running_sections'] = ['footer']

In this first section we will only use the ``footer``. pdfme
will add all of the running_sections referenced in ``running_sections`` list in
the order they are defined, to every page of this section.

And finally we will define the contents of this section, inside ``content1``
list.

.. code-block::

    section1['content'] = content1 = []

We will first add a title for this section:

.. code-block::

    content1.append({
        ".": "A Title", "style": "title", "label": "title1",
        "outline": {"level": 1, "text": "A different title 1"}
    })

The first key in this dictionary we added is what we call in pdfme a dot key,
and is where we place the contents of a paragraph part. We won't extend much
on the format for paragraphs, as it's explained in :class:`pdfme.text.PDFText`
definition, but let's talk about the other keys in this dict. First we have a
``style`` key, with the name of a format that we defined before, that will apply
all of the properties of that format into this paragraph part. We have
a ``label`` key too, defining a position in the PDF document called ``title1``.
Thanks to this we will be able to navigate to this position from any place in
the document, just by using a reference to this label.
Finally, we have an ``outline`` key with a dictionary defining a PDF outline,
a position in the PDF document, to which we can navigate to from the outline
panel of the pdf reader. More information about outlines in
:class:`pdfme.text.PDFText`