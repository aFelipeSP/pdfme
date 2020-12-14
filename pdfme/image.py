from io import BytesIO
from pathlib import Path
import struct
import traceback

class PDFImage:
    def __init__(self, image, extension=None):
        if isinstance(image, str):
            image_bytes = Path(image).open('rb')
            self.image_name = image
            if extension is None:
                extension = image.rpartition('.')[-1]
        elif isinstance(image, Path):
            image_bytes = image.open('rb')
            self.image_name = str(image)
            if extension is None:
                extension = image.suffix
        elif isinstance(image, BytesIO):
            image_bytes = image
            self.image_name = ''
            if extension is None:
                raise TypeError('when image is of type io.BytesIO, extension '
                    'must be provided')
        else:
            raise TypeError('image must be of type str, pathlib.Path or '
                'io.BytesIO')

        if not isinstance(extension, str):
            raise TypeError('extension type is str')

        if len(extension) > 0 and extension[0] == '.':
            extension = extension[1:]

        extension = extension.strip().lower()
        
        if extension in ['jpg', 'jpeg']:
            self.parse_jpg(image_bytes)
        else:
            raise NotImplementedError(('Images of type "{}" are not yet '
                'supported').format(extension))


    def parse_jpg(self, image_bytes):
        try:
            while True:
                markerHigh, markerLow = struct.unpack('BB', image_bytes.read(2))
                if markerHigh != 0xFF or markerLow < 0xC0:
                    raise SyntaxError('No JPEG marker found')
                elif markerLow == 0xDA: # SOS
                    raise SyntaxError('No JPEG SOF marker found')
                elif (markerLow == 0xC8 or # JPG
                    (markerLow >= 0xD0 and markerLow <= 0xD9) or # RSTx
                    (markerLow >= 0xF0 and markerLow <= 0xFD)): # JPGx
                    continue
                else:
                    data_size, = struct.unpack('>H', image_bytes.read(2))
                    data = image_bytes.read(data_size - 2) if data_size > 2 else ''
                    if (
                        (markerLow >= 0xC0 and markerLow <= 0xC3) or # SOF0 - SOF3
                        (markerLow >= 0xC5 and markerLow <= 0xC7) or # SOF4 - SOF7
                        (markerLow >= 0xC9 and markerLow <= 0xCB) or # SOF9 - SOF11
                        (markerLow >= 0xCD and markerLow <= 0xCF) # SOF13 - SOF15
                    ): 
                        depth, h, w, layers = struct.unpack_from('>BHHB', data)

                        if layers == 3: colspace = b'/DeviceRGB'
                        elif layers == 4: colspace = b'/DeviceCMYK'
                        else: colspace = b'/DeviceGray'

                        break
        except Exception:
            traceback.print_exc()
            raise ValueError("Couldn't process image: {}".format(self.image_name))

        image_bytes.seek(0)
        image_data = image_bytes.read()
        image_bytes.close()

        self.width = int(w)
        self.height = int(h)

        self.pdf_obj = {
            'Type': b'/XObject',
            'Subtype': b'/Image',
            'Width': self.width,
            'Height': self.height,
            'ColorSpace': colspace,
            'BitsPerComponent': int(depth),
            'Filter': b'/DCTDecode',
            '__skip_filter__': True,
            '__stream__': image_data
        }

