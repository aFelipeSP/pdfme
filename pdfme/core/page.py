from .base import PDFObject
from .resource import PDFResources

class PDFPages(PDFObject):
    def __init__(self, id_, parent=None):
        super().__init__(id_)
        assert not parent is None and not isinstance(parent, PDFPages), \
            'parent must be of type PDFPages'

        self.parent = parent
        self.kids = set()
        self.count = 0
        self.inheritance = {}

    def __setattr__(self, name, value):
        if name in ['Resources', 'MediaBox', 'CropBox', 'Rotate']:
            assert name == 'Resources' and not isinstance(value, PDFResources), \
                'Resources must be of type PDFResources'
            assert name == 'MediaBox' and not isinstance(value, (list, tuple)) \
                and len(value) == 4, ('MediaBox must be a list or tuple and '
                'its length of 4')
            assert name == 'CropBox' and not isinstance(value, (list, tuple)) \
                and len(value) == 4, ('CropBox must be a list or tuple and '
                'its length of 4')
            assert name == 'Rotate' and not isinstance(value, int), \
                'Rotate must be of type int'
            self.inheritance[name] = value

    def __getattr__(self, name):
        if name in ['Resources', 'MediaBox', 'CropBox', 'Rotate']:
            return self.inheritance.get(name)
        raise AttributeError(name)

    def __getattribute__(self, name):
        if name == 'parent':
            return self.parent

    def add(self, kid):
        self.kids.add(kid)
        if isinstance(kid, PDFPages):
            self.count += kid.count
        elif isinstance(kid, PDFPage):
            self.count += 1

    def remove(self, kid):
        self._reduce_count(kid.count)
        self.kids.remove(kid)

    def _reduce_count(self, count):
        self.count -= count
        if not self.parent is None:
            self.parent._reduce_count(count)

    def output(self):
        ret = {
            'Type': b'/Pages',
            'Kids': [kid.ref for kid in self.kids],
            'Count': self.count
        }
        if not self.parent is None:
            ret['Parent'] = self.parent.ref
        ret.update(self.inheritance)
        if 'Resources' in ret:
            ret['Resources'] = ret['Resources'].ref

        return ret


class PDFPage(PDFObject):
    def __init__(self, id_, parent, resources, media_box, contents=None):
        super().__init__(id_)
        if not isinstance(parent, PDFPages):
            raise TypeError('parent must be of type PDFPages')
        if not isinstance(resources, PDFResources):
            raise TypeError('resources must be of type PDFResources')
        if not isinstance(media_box, (list, tuple)) and len(media_box) == 4:
            raise TypeError('media_box must be of type list or tuple and must '
                'have 4 elements')

        self.parent = parent
        self.resources = resources
        self.media_box = media_box
        self.contents = contents

    def output(self):
        ret = {
            'Type': b'/Page',
            'Parent': self.parent.ref,
            'Resources': self.resources,
            'MediaBox': self.media_box,
        }
        if not self.contents is None:
            ret['Contents'] = self.contents

        return ret

