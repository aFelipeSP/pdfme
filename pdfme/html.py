from xml.etree import ElementTree as ET
from html5lib.html5parser import parse

import cssselect2
import tinycss2
from jinja2 import Template

from .css import parse_css_rule
from .base import PDFBase
from .utils import subs

class HTML2PDF:
    def __init__(self, html, context={}):
        
        # self.pdf = PDFBase()
        # root_i, self.root = self.pdf.add({'Type': b'/Catalog'})
        # self.pdf.trailer['Root'] = ref(root_i)
        self.parse_html(html, context)

    def parse_html(self, template, context={}):
        html = Template(template).render(context)
        html_root = parse(html, namespaceHTMLElements=False)
        # html_root = ET.fromstring(html)

        self.css_matcher = cssselect2.Matcher()

        stylesheet = '\n'.join(el.text for el in html_root.findall('./head/style'))

        rules = tinycss2.parse_stylesheet(stylesheet, True, True)

        for rule in rules:
            selectors = cssselect2.compile_selector_list(rule.prelude)
            # selector_string = tinycss2.serialize(rule.prelude)
            # content_string = tinycss2.serialize(rule.content)
            # payload = (selector_string, content_string)
            for selector in selectors:
                self.css_matcher.add_selector(selector, rule.content)

        body = html_root.find('body')

        wrapper = cssselect2.ElementWrapper.from_html_root(body)
        self.iter_children(wrapper)

    def iter_children(self, element):
        for child in element.iter_children():
            matches = self.css_matcher.match(child)
            if matches:
                for match in matches:
                    attrs = parse_css_rule(match[3])
                    print(attrs)

        print(element.tail.strip())


    def output(self, *args, **kwargs):
        self.pdf.output(*args, **kwargs)
