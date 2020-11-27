from html.parser import HTMLParser

from jinja2 import Template

from .pdfbase import PDFBase

from .utils import subs, ref


class HTML2PDF(HTMLParser):
    def __init__(self, html, context={}):
        super().__init__()
        self.tag = []
        self.meta = {}
        self.style = {}
        self.attrs = {}
        self.content = []
        html_ready = Template(html).render(context)
        self.pdf = PDFBase()

        root = self.pdf.add({
            'Type': b'/Catalog'
        })

        self.pdf.trailer['Root'] = ref(root)

        self.feed(html_ready)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = dict(attrs)
        self.tags.append(tag)
        if self.tag == ['html', 'head', 'meta'] and 'name' in attrs and 'content' in attrs:
            self.meta[attrs['name']] = attrs['content']

        self.attrs = attrs

    def handle_endtag(self, tag):
        self.tags.pop()

    def handle_data(self, data):
        pass

    def output(self, *args, **kwargs):
        self.pdf.output(*args, **kwargs)


#         <meta charset="UTF-8">
# Define keywords for search engines:

# <meta name="keywords" content="HTML, CSS, JavaScript">
# Define a description of your web page:

# <meta name="description" content="Free Web tutorials">
# Define the author of a page:

# <meta name="author" content="John Doe">

# <meta name="viewport" content="width=device-width, initial-scale=1.0">