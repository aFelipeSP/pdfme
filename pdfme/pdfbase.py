from io import BytesIO
from uuid import uuid4

from .objects import parse_obj
from .utils import subs

class PDFBase:
    def __init__(self, version='1.3', trailer=None):
        self.version = version
        self.content = []
        if trailer is None:
            self.trailer = {}
        elif not isinstance(trailer, dict):
            raise ValueError('trailer must be a dict')
        else:
            self.trailer = trailer
        self.count = 1

    def add(self, obj):
        self.content.append(obj)
        self.count += 1
        return self.count - 1, obj

    def __getitem__(self, i):
        if i == 0: return None
        return self.content[i - 1]

    def __setitem__(self, i, value):
        if i > 0:
            self.content[i] = value

    def __iter__(self):
        for el in [None] + self.content:
            yield el

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

            bytes_ = subs('{} 0 obj\n', i + 1) + parse_obj(obj) + '\nendobj\n'.encode('latin')
            count += len(bytes_)
            buffer.write(bytes_)

        self.trailer['Size'] = self.count
        if 'ID' not in self.trailer:
            id_ = lambda: b'<' + str(uuid4()).replace('-', '').encode('latin') + b'>'
            self.trailer['ID'] = [id_(), id_()]
        trailer = parse_obj(self.trailer)

        footer = '\nstartxref\n{}\n%%EOF'.format(count + 1)

        buffer.write((xref + 'trailer\n').encode('latin') + trailer + footer.encode('latin'))