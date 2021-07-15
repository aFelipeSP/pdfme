import struct
import traceback
from io import BytesIO, BufferedReader
from pathlib import Path
from typing import Union

ImageType = Union[str, Path, BytesIO]
class PDFImage:
    """Class that represents a PDF image.

    You can pass the location path (``str`` or ``pathlib.Path`` format) of the
    image, or pass a file-like object (``io.BytesIO``) with the image bytes, the
    extension of the image, and the image name.

    Only JPEG image format is supported in this moment.

    Args:
        image (str, pathlib.Path, BytesIO): The path or file-like object of the
            image.
        extension (str, optional): If ``image`` is path-like object, this
            argument should contain the extension of the image.
        image_name (str, optional): If ``image`` is path-like object, this
            argument should contain the name of the image. This name should be
            unique among the images added to the same PDF document.
    """
    def __init__(
        self, image: ImageType, extension: str=None, image_name: str=None
    ):
        image_bytes = None
        try:
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
                if image_name is None:
                    raise TypeError(
                        'when image is of type io.BytesIO, image_name must be '
                        'provided'
                    )
                self.image_name = image_name
                if extension is None:
                    raise TypeError(
                        'when image is of type io.BytesIO, extension must be '
                        'provided'
                    )
            else:
                raise TypeError(
                    'image must be of type str, pathlib.Path or io.BytesIO'
                )

            if not isinstance(extension, str):
                raise TypeError('extension type is str')

            if len(extension) > 0 and extension[0] == '.':
                extension = extension[1:]

            extension = extension.strip().lower()

            if extension in ['jpg', 'jpeg']:
                self.parse_jpg(image_bytes)
            else:
                raise NotImplementedError(
                    'Images of type "{}" are not yet supported'.format(extension)
                )
        finally:
            if image_bytes is not None:
                image_bytes.close()

    def parse_jpg(self, bytes_: Union[BytesIO, BufferedReader]) -> None:
        """Method to extract metadata from a JPEG image ``bytes_`` needed to
        embed this image in a PDF document.

        This method creates this instance's attibute ``pdf_obj``, containing
        a dict that can be added to a :class:`pdfme.base.PDFBase` instance as
        a PDF Stream object that represents this image.

        Args:
            bytes_ (BytesIO, BufferedReader): A file-like object containing the
                image.
        """
        try:
            while True:
                markerHigh, markerLow = struct.unpack('BB', bytes_.read(2))
                if markerHigh != 0xFF or markerLow < 0xC0:
                    raise SyntaxError('No JPEG marker found')
                elif markerLow == 0xDA: # SOS
                    raise SyntaxError('No JPEG SOF marker found')
                elif (markerLow == 0xC8 or # JPG
                    (markerLow >= 0xD0 and markerLow <= 0xD9) or # RSTx
                    (markerLow >= 0xF0 and markerLow <= 0xFD)): # JPGx
                    continue
                else:
                    data_size, = struct.unpack('>H', bytes_.read(2))
                    data = bytes_.read(data_size - 2) if data_size > 2 else ''
                    if (
                        (markerLow >= 0xC0 and markerLow <= 0xC3) or #SOF0-SOF3
                        (markerLow >= 0xC5 and markerLow <= 0xC7) or #SOF4-SOF7
                        (markerLow >= 0xC9 and markerLow <= 0xCB) or #SOF9-SOF11
                        (markerLow >= 0xCD and markerLow <= 0xCF) #SOF13-SOF15
                    ):
                        depth, h, w, layers = struct.unpack_from('>BHHB', data)

                        if layers == 3: colspace = b'/DeviceRGB'
                        elif layers == 4: colspace = b'/DeviceCMYK'
                        else: colspace = b'/DeviceGray'

                        break
        except Exception:
            traceback.print_exc()
            raise ValueError(
                "Couldn't process image: {}".format(self.image_name)
            )

        bytes_.seek(0)
        image_data = bytes_.read()
        bytes_.close()

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

