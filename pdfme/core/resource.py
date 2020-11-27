from .base import PDFObject
from .font import PDFFont
from ..utils import subs


class PDFResources(PDFObject):
    def __init__(self, id_):
        super().__init__(id_)
        self.ext_g_state = {}
        self.x_object = {}
        self.font = {}

        self.font_counter = 0

    def add_font(self, font, name=None):
        if not isinstance(font, PDFFont):
            TypeError('font must be of type PDFFont')
        if name is None:
            while ('F' + str(self.__dict__['font_counter'])) in self.__dict__['font']:
                self.font_counter += 1
            name = 'F' + str(self.__dict__['font_counter'])
        elif not isinstance(name, str):
            TypeError('name must be of type str')

        if name in self.__dict__['font']:
            Exception(str(name) + ' is already in fonts dictionary')

        self.__dict__['font'][name] = font

    def remove_font(self, name):
        if not isinstance(name, str):
            TypeError('name must be of type str')
        self.__dict__['font'].pop(name)

    def __setattr__(self, name, value):
        raise Exception("can't change attributes")

    def __getattr__(self, name):
        raise Exception(str(name) + " not in this obj")

    def __getattribute__(self, name):
        raise Exception("can't get attributes")

    def output(self):
        ret = {
            'ExtGState': {subs('/{}', k): v.ref for k, v in self.ExtGState.items()},
            'XObject': {subs('/{}', k): v.ref for k, v in self.XObject.items()},
            'Font': {subs('/{}', k): v.ref for k, v in self.Font.items()}
        }

        return ret