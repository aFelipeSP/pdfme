from ..utils import ref

class PDFObject:
    def __init__(self, id_):
        self.id = id_

    @property
    def ref(self):
        return ref(self.id)


# class PDFObjectGeneric(PDFObject):
#     def __init__(self, id_, required, optionals):
#         super().__init__(id_)
#         self.required = required
#         self.optionals = optionals

#     def __setattr__(self, name, value):
#         if name in ['Resources', 'MediaBox', 'CropBox', 'Rotate']:
#             self.inheritance[name] = value

#     def __getattr__(self, name):
#         if name in ['Resources', 'MediaBox', 'CropBox', 'Rotate']:
#             return self.inheritance[name]
#         raise AttributeError(name)

#     def __getattribute__(self, name):
#         if name == 'parent':
#             return self.parent

#     def output(self):


