from io import BytesIO
from uuid import uuid4

from .objects import parse_obj
from .utils import subs

def unique_id():
    return str(uuid4()).replace('-', '')

class PDFBase:
    def __init__(self, root, version='1.3', info=False):
        self.version = version
        self.content = [root]
        self.count = 2
        self.i = 0

        self.info = info
        if info != False:
            self.add(info)

    def add(self, obj):
        self.content.append(obj)
        self.count += 1
        return self.count - 1

    def __getitem__(self, i):
        if i == 0: return None
        return self.content[i - 1]

    def __setitem__(self, i, value):
        if i > 0:
            self.content[i] = value

    def __iter__(self):
        for el in [None] + self.content:
            yield el

    # def __next__(self):
    #     if self.i < len(self.content):
            
    #         self.i += 1
    #         return self.content[self.i - 1]
    #     self.i = 0
    #     raise StopIteration()

    def __len__(self):
        return len(self.content)

    def __str__(self):
        return str(self.content)

    def __repr__(self):
        return str(self.content)

    def output(self, buffer):
        header = subs('%PDF-{}\n%%\x129\x129\x129\n', self.version)
        count = len(header)
        buffer.write(header)

        xref = '\nxref\n0 {}\n0000000000 65535 f \n'.format(self.count)

        for i, obj in enumerate(self.content):
            xref += str(count).zfill(10) + ' 00000 n \n'

            bytes_ = subs('{} 0 obj\n', i + 1) + parse_obj(obj) + '\nendobj\n'.encode()
            count += len(bytes_)
            buffer.write(bytes_)


        footer = xref + 'trailer\n<</Size {}/Root 1 0 R'.format(self.count)
        if self.info:
            footer += '/Info 2 0 R'
        
        footer += '/ID [<{}><{}>]>>\nstartxref\n{}\n%%EOF'.format(
            unique_id(), unique_id(), count + 1)
        
        buffer.write(footer.encode())