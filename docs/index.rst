
pdfme
=====

You can use this library to create PDF documents by using one of the following
strategies:

* Use the function :func:`pdfme.document.build_pdf`, passing a dictionary with
  the description of the document as its argument. For more information about
  this approach see :class:`pdfme.document.PDFDocument`.

* Use the :class:`pdfme.pdf.PDF` class and use its methods to build the PDF
  document. For more information about this approach see :class:`pdfme.pdf.PDF`
  class definition.

You can explore the rest of this library components in the following links:

.. toctree::
   :maxdepth: 3

   modules


Shortcomings
============

* Currently this library only supports the standard 14 PDF fonts. 
* Currently the only image format supported is ``jpg``.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
