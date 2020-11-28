
# def validate_rule(rule)

# background-color
# border-bottom-color, border-bottom-style, border-bottom-width
# border-left-color, border-left-style, border-left-width
# border-right-color, border-right-style, border-right-width
# border-top-color, border-top-style, border-top-width
# colordisplay
# font-family, font-size, font-style, font-weight
# height
# line-height, list-style-type
# margin-bottom, margin-left, margin-right, margin-top
# padding-bottom, padding-left, padding-right, padding-top
# page-break-after, page-break-before
# size
# text-align, text-decoration, text-indent
# vertical-align
# white-space
# width


def parse_css_rule(css_rule):
    attrs = {}
    rule = {}
    failed = False
    saving_content = False
    for token in css_rule:
        if token.type == 'whitespace':
            continue
        elif token == ';':
            if not failed:
                attrs[rule['name']] = rule['content']
            saving_content = False
            failed = False
            rule = {}
        elif failed:
            continue
        elif not saving_content and token.type == 'ident':
            if not 'name' in rule:
                rule['name'] = token.value
            else:
                failed = True
        elif token == ':':
            if saving_content:
                failed = True
            else:
                saving_content = True
        else:
            if not saving_content:
                failed = True
            else:
                rule.setdefault('content', [])
                rule['content'].append(token)

    if not failed and 'name' in rule and 'content' in rule:
        attrs[rule['name']] = rule['content']

    return attrs