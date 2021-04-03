from utils import gen_rich_text
from pdfme import PDF

# from pdfme import text1 as t
# from pdfme import standard_fonts as s

content = gen_rich_text(5000)

# content = 'wert dfg asd yudtuy asdfasdg asf fh yuoi qwerwqwer vzx fukesrt ui awer fjtyi afaf tyuktyur rtewqaa vbxcgbkdf sdfghss'

# t = t.PDFText(content, s.STANDARD_FONTS)
# t.run()
# t.build(25, 500)

pdf = PDF()
rect = '0.9 0.9 0.9 rg {} {} {} {} re F'.format(pdf.margin['left'], pdf.margin['bottom'], pdf.width,pdf.height)
pdf.stream(rect)
# pdf.image('puppy.jpg')
ret = pdf.text(content, text_align='l')
# ret = pdf.list([gen_rich_text(500) for i in range(10)], list_style='number')

while not ret is None:
    pdf.add_page()
    pdf.stream(rect)
    ret = pdf.text(ret, text_align='l')

with open('test.pdf', 'wb') as f:
    pdf.output(f)