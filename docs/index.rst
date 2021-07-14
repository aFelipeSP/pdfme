
pdfme
=====
This is a powerful library to create PDF documents easily.

Main features
-------------

* You can create a document without having to worry about the position of each
  element in the document. But you have the possibility to place any element
  wherever you want too.

* You can add rich text paragraphs (paragraphs with text in different sizes,
  fonts, colors and styles).

* You can add tables and place whatever you want on their cells, span columns
  and rows, and change the fills and borders in the easiest way possible.

* You can add content boxes, a multi-column element where you can add
  paragraphs, images, tables and even content boxes themselves. The elements inside this
  content boxes are added from top to bottom and from left to right.

* You can add url links (to web pages), labels/references and footnotes anywhere
  in the document.

* You can add running sections, content boxes that will be included in every
  page you add to the document. Headers and footers are the most common running
  sections, but you can add running sections anywhere in the page.


Installation
------------
You can install using pip:

.. code-block::

  pip install pdfme


Usage
-----

You can use this library to create PDF documents by using one of the following
strategies:

* The recommended way is to use the function :func:`pdfme.document.build_pdf`,
  passing a dictionary with the description of the document as its argument.
  For more information about this approach see
  :class:`pdfme.document.PDFDocument`.

* Use the :class:`pdfme.pdf.PDF` class and use its methods to build the PDF
  document. For more information about this approach see :class:`pdfme.pdf.PDF`
  class definition.

  
  
Shortcomings
------------

* Currently this library only supports the standard 14 PDF fonts. 
* Currently the only image format supported is ``jpg``.

You can explore the rest of this library components in the following links:
  
.. toctree::
    :maxdepth: 3

    examples
    modules

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
