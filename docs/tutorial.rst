Tutorial
========

In this tutorial we will create a PDF document using pdfme to showcase some
of its functionalities.

We will use the preferred way to build a document in pdfme, that is using
:func:`pdfme.document.build_pdf` function. This function receives as its first
argument a nested dict structure with the contents and styling of the document,
and most of this tutorial will be focused on building this dict.

In every step we will tell you the class or function definition where you
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
        'margin_bottom': 15,
        'text_align': 'j'
    }


In our example we define the ``margin_bottom`` property, that will be the
default space below every element in the document, and ``text_align`` will
be the default text alignment for all the paragraphs in the document.
In this dict you can set the default value for the style properties that affect
the paragraphs (``text_align``, ``line_height``, ``indent``, ``list_text``,
``list_style``, ``list_indent``, ``b``, ``i``, ``s``, ``f``, ``u``, ``c``,
``bg``, ``r``), images (``image_place``), tables (``cell_margin``,
``cell_margin_left``, ``cell_margin_top``, ``cell_margin_right``,
``cell_margin_bottom``, ``cell_fill``, ``border_width``, ``border_color``,
``border_style``) and content boxes (``margin_top``, ``margin_left``,
``margin_bottom``, ``margin_right``) inside the document.
For information about paragraph properties see :class:`pdfme.text.PDFText`,
about table properties see :class:`pdfme.table.PDFTable`, and about image and
content properties see :class:`pdfme.content.PDFContent`.

You can set page related properties in ``style`` too, like ``page_size``,
``rotate_page``, ``margin``, ``page_numbering_offset`` and
``page_numbering_style`` (see :class:`pdfme.pdf.PDF` definition).

You can also define named style instructions or formats (something like CSS
classes) in the ``document`` dict like this:

.. code-block::

    document['formats'] = {
        'url': {'c': 'blue', 'u': 1},
        'title': {'b': 1, 's': 13}
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

    document['running_sections'] = {
        'header': {
            'x': 'left', 'y': 20, 'height': 'top',
            'style': {'text_align': 'r'},
            'content': [{'.b': 'This is a header'}]
        },
        'footer': {
            'x': 'left', 'y': 800, 'height': 'bottom',
            'style': {'text_align': 'c'},
            'content': [{'.': ['Page ', {'var': '$page'}]}]
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
them, or add a ``per_page`` dictionary like this:

.. code-block::

    document['per_page'] = [
        {'pages': '1:1000:2', 'style': {'margin': [60, 100, 60, 60]}},
        {'pages': '0:1000:2', 'style': {'margin': [60, 60, 60, 100]}},
        {'pages': '0:4:2', 'running_sections': {'include': ['header']}},
    ]

This dictionary will style, include or exclude running sections from the pages
you set in the property ``pages``. This key is a string of comma separated
ranges of pages, and in this particular case we will add ``header`` to pages 0
and 2, and will add more left margin in odd pages, and more right margin in even
pages.
To know more about ``per_page`` dict see :class:`pdfme.document.PDFDocument`.
Keep reading to see how we add ``header`` and ``footer`` per sections.

Finally we are going to talk about *sections*. These can have their own page
layout, page numbering, running sections and style, and are the places where we
define the contents of the document. It's important to note that after every
section there's a page break.

Let's create ``sections`` list to contain the documents sections, and add
our first section ``section1``.

.. code-block::

    document['sections'] = []
    section1 = {}
    document['sections'].append(section1)

A section is just a content box, a multi-column element where you can add
paragraphs, images, tables and even content boxes themselves (see 
:class:`pdfme.content.PDFContent` for more informarion about content boxes).
pdfme will put every element from a section in the PDF document from top to 
bottom, and when the first page is full it will add a new page to keep
adding elements to the document, and will keep adding pages until all of the
elements are inside the document.

Like a regular content box you can add a ``style`` key to a section, where you
can reference a format (from the ``formats`` dict we created before), or add a
new ``style`` dict, and with this you can overwrite any of the default style
properties of the document.

.. code-block::

    section1['style'] = {
        'page_numbering_style': 'roman'
    }

Here we overwrite only ``page_numbering_style``, a property that sets the style
of the page numbers inside the section (see :class:`pdfme.pdf.PDF` definition).
Default value is ``arabic`` style, and here we change it to ``roman`` (at least
for this section).

Now we are going to reference the running sections that we will use in this
section.

.. code-block::

    section1['running_sections'] = ['footer']

In this first section we will only use the ``footer``. pdfme
will add all of the running_sections referenced in ``running_sections`` list, in
the order they are in this list, to every page of this section.

And finally we will define the contents of this section, inside ``content1``
list.

.. code-block::

    section1['content'] = content1 = []

We will first add a title for this section:

.. code-block::

    content1.append({
        '.': 'A Title', 'style': 'title', 'label': 'title1',
        'outline': {'level': 1, 'text': 'A different title 1'}
    })

We added a paragraph dict, and it's itself what we call a paragraph part. A
paragraph part can have other nested paragraph parts, as it's explained in
:class:`pdfme.text.PDFText` definition. This is like an HTML structure, where
you can define a style in a root element and its style will be passed to all of
its descendants.

The first key in this dictionary we added is what we call a dot key,
and is where we place the contents of a paragraph part, and its descendants.
We won't extend much on the format for paragraphs, as it's explained in
:class:`pdfme.text.PDFText` definition, so let's talk about the other keys in
this dict. First we have a ``style`` key, with the name of a format that we
defined before in the document's ``formats`` dict. This will apply all of the
properties of that format into this paragraph part. We have a ``label`` key too,
defining a position in the PDF document called ``title1``.
Thanks to this we will be able to navigate to this position from any place in
the document, just by using a reference to this label (keep reading to see how
we reference this title in the second section).
Finally, we have an ``outline`` key with a dictionary defining a PDF outline,
a position in the PDF document, to which we can navigate to from the outline
panel of the pdf reader. More information about outlines in
:class:`pdfme.text.PDFText`.

Now we will add our first paragraph.

.. code-block::

    content1.append(
        ['This is a paragraph with a ', {'.b;c:green': 'bold green part'}, ', a ',
        {'.': 'link', 'style': 'url', 'uri': 'https://some.url.com'},
        ', a footnote', {'footnote': 'description of the footnote'},
        ' and a reference to ',
        {'.': 'Title 2.', 'style': 'url', 'ref': 'title2'}]
    )

Note that this paragraph is not a dict, like the title we added before. Here we
use a list of paragraph parts, a shortcut when you have a paragraph with 
different styles or with labels, references, urls, outlines or footnotes.

We give format to the second paragraph part by using its dot key. This way of
giving format to a paragraph part is something like the inline styles in HTML
elements, and in particular in this example we are making the text inside this
part bold and green.

The rest of this list paragraph parts are examples of how to add a url,
a footnote and a reference (clickable links to go to the location in the
document of the label we reference) to the second title of this document (
located in the second section).

Next we will add an image to the document, located in the relative path
``path/to/some_image.jpg``.

.. code-block::

    content1.append({
        'image': 'path/to/some_image.jpg',
        'style': {'margin_left': 100, 'margin_right': 100}
    })

    
In ``style`` dict we set ``margin_left`` and ``margin_right`` to 100
to make our image narrower and center it in the page.

Next we will add a group element, containing an image and a paragraph with the
image description. This guarantees that both the image and its description will
be placed in the same page. To know more about group elements, and how to
control the its height check :class:`pdfme.content.PDFContent`.

.. code-block::

    content1.append({
        "style": {"margin_left": 80, "margin_right": 80},
        "group": [
            {"image": 'path/to/some_image.jpg'},
            {".": "Figure 1: Description of figure 1"}
        ]
    })

Next we will add our first table to the document, a table with summary
statistics from a database table.

.. code-block::

    table_def1 = {
        'widths': [1.5, 1, 1, 1],
        'style': {'border_width': 0, 'margin_left': 70, 'margin_right': 70},
        'fills': [{'pos': '1::2;:', 'color': 0.7}],
        'borders': [{'pos': 'h0,1,-1;:', 'width': 0.5}],
        'table': [
            ['', 'column 1', 'column 2', 'column 3'],
            ['count', '2000', '2000', '2000'],
            ['mean', '28.58', '2643.66', '539.41'],
            ['std', '12.58', '2179.94', '421.49'],
            ['min', '1.00', '2.00', '1.00'],
            ['25%', '18.00', '1462.00', '297.00'],
            ['50%', '29.00', '2127.00', '434.00'],
            ['75%', '37.00', '3151.25', '648.25'],
            ['max', '52.00', '37937.00', '6445.00']
        ]
    }

    content1.append(table_def1)

In ``widths`` list we defined the width for every column in the table. The
numbers here are not percentages or fractions but proportions. For example,
in our table the first column is 1.5 times larger than the second one, and
the third and fourth one are the same length as the second one.

In ``style`` dict we set the ``border_width`` of the table to 0, thus hiding
all of this table lines. We also set ``margin_left`` and ``margin_right`` to 70
to make our table narrower and center it in the page.

In ``fills`` we overwrite the default value of ``cell_fill``, for some of the
rows in the table. The format of this ``fills`` list is explained in
:class:`pdfme.table.PDFTable` definition, but in short, we are setting the fill
color of the even rows to a gray color.

In ``borders`` we overwrite the default value of ``border_width`` (which we set
to 0 in ``style``) for some of the horizontal borders in the table. The format
of this ``borders`` list is explained in :class:`pdfme.table.PDFTable`
definition too, but in short, we are setting the border width of the first,
second and last horizontal borders to 0.5.

And finally we are adding the table contents in the ``table`` key. Each list,
in this ``table`` list, represents a row of the table, and each element in a row
list represents a cell.

Next we will add our second table to the document, a form table with some
cells combined.

.. code-block::

    table_def2 = {
        'widths': [1.2, .8, 1, 1],
        'table': [
            [
                {
                    'colspan': 4,
                    'style': {
                        'cell_fill': [0.8, 0.53, 0.3],
                        'text_align': 'c'
                    },
                    '.b;c:1;s:12': 'Fake Form'
                },None, None, None
            ],
            [
                {'colspan': 2, '.': [{'.b': 'First Name\n'}, 'Fakechael']}, None,
                {'colspan': 2, '.': [{'.b': 'Last Name\n'}, 'Fakinson Faker']}, None
            ],
            [
                [{'.b': 'Email\n'}, 'fakeuser@fakemail.com'],
                [{'.b': 'Age\n'}, '35'],
                [{'.b': 'City of Residence\n'}, 'Fake City'],
                [{'.b': 'Cell Number\n'}, '33333333333'],
            ]
        ]
    }

    content1.append(table_def2)

In the first row we combined the 4 columns to show the title of the form; in
the second row we combine the first 2 columns for the first name, and the other
2 columns for the last name; and in the last row we use the four cells to the
rest of the information.

Notice that cells that are below or to the right of a merged cell must be equal
to ``None``, and that instead of using strings inside the cells, like we did
in the first table, we used paragraph parts in the cells. And besides paragraphs
you can add a content box, an image or even another table to a cell. 

Now we will add a second section.

.. code-block::

    document['sections'].append({
        'style': {
            'page_numbering_reset': True, 'page_numbering_style': 'arabic'
        },
        'running_sections': ['header', 'footer'],
        'content': [

            {
                '.': 'Title 2', 'style': 'title', 'label': 'title2',
                'outline': {}
            },

            {
                'style': {'list_text': '1.  '},
                '.': ['This is a list paragraph with a reference to ',
                {'.': 'Title 1.', 'style': 'url', 'ref': 'title1'}]
            }
        ]
    })

In this section we set the page numbering style back to the default value,
``arabic``, and we reset the page count to 1 by including
``page_numbering_reset`` in the ``style`` dict.

We also added running section ``header``, additional to the running section
``footer`` we used in the first section.

And we added the second title of the document, with its label and outline, and a
list paragraph (a paragraph with text ``'1.  '`` on the left of the paragraph)
with a reference to the first title of the document.

Finally, we will generate the PDF document from the dict ``document`` we just
built, by using ``build_pdf`` function.

.. code-block::

    with open('document.pdf', 'wb') as f:
        build_pdf(document, f)

Following these steps we will have a PDF document called ``document.pdf`` with
all of the contents we added to ``document`` dict.