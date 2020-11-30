import xml.etree.ElementTree as ET

from pdfme.pdf import HTML2PDF

root = '''<html>
<head>
<title>
A Simple HTML Document
</title>
<style>
.asdf {
  border: 1px solid #dddddd;
  text-align: right;
  padding: 8px;
}
</style>
<style>
.qwer {color: #456;}
</style>
</head>
<body>
<p class="asdf qwer" style="color:#457">This is a very<span>sdaf</span> simple HTML document</p>
<p>It only has two paragraphs</p>
</body>
</html>'''


HTML2PDF(root)
