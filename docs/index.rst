
pdfme
=====
This is a powerful library to create PDF documents easily.

The way you create a PDF document with pdfme is very similar to how you create
documents with LaTex: you just tell pdfme at a very high level what elements you
want to be in the document, without worrying about wrapping text in a box,
positioning every element inside the page, creating the lines of a table, or the
internals of the PDF Document Format. pdfme will put every element
below the last one, and when a page is full it will add a new page to keep
adding elements to the document, and will keep adding pages until all of the
elements are inside the document. It just works.

If you want the power to place elements wherever you want and mess with the PDF
Document Format internals, pdfme got you covered too. Give the docs a look to
check how you can do this.

Main features
-------------

* You can create a document without having to worry about the position of each
  element in the document. But you have the possibility to place any element
  wherever you want too.

* You can add rich text paragraphs (paragraphs with text in different sizes,
  fonts, colors and styles).

* You can add images.

* You can add tables and place whatever you want on their cells, span columns
  and rows, and change the fills and borders in the easiest way possible.

* You can add group elements that contain paragraphs, images or tables, and
  guarantee that all of the children elements in the group element will be in
  the same page.

* You can add content boxes, a multi-column element where you can add
  paragraphs, images, tables and even content boxes themselves. The elements
  inside this content boxes are added from top to bottom and from left to right.

* You can add url links (to web pages), labels/references, footnotes and
  outlines anywhere in the document.

* You can add running sections, content boxes that will be included in every
  page you add to the document. Headers and footers are the most common running
  sections, but you can add running sections anywhere in the page.


Installation
------------
You can install using pip:

.. code-block::

  pip install pdfme

About this docs
---------------

We recommend starting with the tutorial in :doc:`tutorial`, but you can find
the description and instructions for each feature inside the docs for each 
class representing the feature, so in :class:`pdfme.text.PDFText` class you'll
learn how to build a paragraph, in :class:`pdfme.table.PDFTable` class you'll
learn how to build a table, in :class:`pdfme.content.PDFContent` class you'll
learn how to build a content box, in :class:`pdfme.document.PDFDocument` class
you'll learn how to build a PDF from a nested-dict structure (Json) and in
:class:`pdfme.pdf.PDF` class you'll learn how to use the main class of this
library, the one that represents the PDF document.

Usage
-----

You can use this library to create PDF documents by using one of the following
strategies:

* The recommended way is to use the function :func:`pdfme.document.build_pdf`,
  passing a dictionary with the description and styling of the document as its
  argument. :doc:`tutorial` section uses this method to build a PDF document,
  and you can get more information about this approach in
  :class:`pdfme.document.PDFDocument` definition.

* Use the :class:`pdfme.pdf.PDF` class and use its methods to build the PDF
  document. For more information about this approach see :class:`pdfme.pdf.PDF`
  class definition.
  
Shortcomings
------------

* Currently this library only supports the standard 14 PDF fonts. 
* Currently this library only supports ``jpg`` and ``png`` image formats (png
  images are converted to jpg images using Pillow, so you have to install it to
  be able to embed png images).

You can explore the rest of this library components in the following links:
  
.. toctree::
    :maxdepth: 3

    tutorial
    examples
    modules

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
