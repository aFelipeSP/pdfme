# pdfme

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

## Main features

* You can create a document without having to worry about the position of each
  element in the document. But you have the possibility to place any element
  wherever you want too.
* You can add rich text paragraphs (paragraphs with text in different sizes,
  fonts, colors and styles).
* You can add tables and place whatever you want on their cells, span columns
  and rows, and change the fills and borders in the easiest way possible. 
* You can add content boxes, a multi-column element where you can add 
  paragraphs, images, tables and even content boxes themselves. The elements
  inside this content boxes are added from top to bottom and from left to right.
* You can add url links (to web pages), labels/references, footnotes and
  outlines anywhere in the document.
* You can add running sections, content boxes that will be included in every
  page you add to the document. Headers and footers are the most common running
  sections, but you can add running sections anywhere in the page.
## Installation

You can install using pip:
```
pip install pdfme
```

## Documentation

* Docs and examples: https://pdfme.readthedocs.io

