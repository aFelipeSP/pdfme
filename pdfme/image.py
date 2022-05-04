import struct
import traceback
from io import BytesIO, BufferedIOBase
from pathlib import Path
from typing import Optional, Union, BinaryIO

ImageType = Union[str, Path, BufferedIOBase]


class PDFImage:
    """Class that represents a PDF image.

    You can pass the location path (``str`` or ``pathlib.Path`` format) of the
    image, or pass a file-like object (``io.BufferedIOBase``) with the image bytes, the
    extension of the image, and the image name.

    Only JPEG and PNG image formats are supported in this moment. PNG images are
    converted to JPEG, and for this Pillow library is required.

    Args:
        image (str, pathlib.Path, BufferedIOBase): The path or file-like object of the
            image.
        extension (str, optional): If ``image`` is path-like object, this
            argument should contain the extension of the image. Options are
            [``jpg``, ``jpeg``, ``png``].
        image_name (str, optional): If ``image`` is path-like object, this
            argument should contain the name of the image. This name should be
            unique among the images added to the same PDF document.
    """

    def __init__(self, image: ImageType, extension: str = None, image_name: str = None):
        image_bytes = None
        try:
            if isinstance(image, str):
                image_bytes = Path(image).open("rb")
                self.image_name = image
                if extension is None:
                    extension = image.rpartition(".")[-1]
            elif isinstance(image, Path):
                image_bytes = image.open("rb")
                self.image_name = str(image)
                if extension is None:
                    extension = image.suffix
            elif isinstance(image, BufferedIOBase):
                image_bytes = image
                if image_name is None:
                    raise TypeError(
                        "when image is of type io.BufferedIOBase, image_name must be "
                        "provided"
                    )
                self.image_name = image_name
                if extension is None:
                    raise TypeError(
                        "when image is of type io.BufferedIOBase, extension must be "
                        "provided"
                    )
            else:
                raise TypeError(
                    "image must be of type str, pathlib.Path or io.BufferedIOBase"
                )

            if not isinstance(extension, str):
                raise TypeError("extension type is str")

            if len(extension) > 0 and extension[0] == ".":
                extension = extension[1:]

            extension = extension.strip().lower()

            if extension in ["jpg", "jpeg"]:
                self.parse_jpg(image_bytes)
            elif extension == "png":
                self.parse_png(image_bytes)
            else:
                raise NotImplementedError(
                    'Images of type "{}" are not yet supported'.format(extension)
                )
        finally:
            if not isinstance(image, BufferedIOBase) and image_bytes is not None:
                image_bytes.close()

    def parse_jpg(self, bytes_: BufferedIOBase) -> None:
        """Method to extract metadata from a JPEG image ``bytes_`` needed to
        embed this image in a PDF document.

        This method creates this instance's attibute ``pdf_obj``, containing
        a dict that can be added to a :class:`pdfme.base.PDFBase` instance as
        a PDF Stream object that represents this image.

        Args:
            bytes_ (BufferedIOBase): A file-like object containing the
                image.
        """
        try:
            while True:
                markerHigh, markerLow = struct.unpack("BB", bytes_.read(2))
                if markerHigh != 0xFF or markerLow < 0xC0:
                    raise SyntaxError("No JPEG marker found")
                elif markerLow == 0xDA:
                    raise SyntaxError("No JPEG SOF marker found")
                elif (
                    markerLow == 0xC8
                    or (markerLow >= 0xD0 and markerLow <= 0xD9)
                    or (markerLow >= 0xF0 and markerLow <= 0xFD)
                ):
                    continue
                else:
                    (data_size,) = struct.unpack(">H", bytes_.read(2))
                    data = bytes_.read(data_size - 2) if data_size > 2 else b""
                    if (
                        (markerLow >= 0xC0 and markerLow <= 0xC3)
                        or (markerLow >= 0xC5 and markerLow <= 0xC7)
                        or (markerLow >= 0xC9 and markerLow <= 0xCB)
                        or (markerLow >= 0xCD and markerLow <= 0xCF)
                    ):
                        depth, h, w, layers = struct.unpack_from(">BHHB", data)

                        if layers == 3:
                            colspace = b"/DeviceRGB"
                        elif layers == 4:
                            colspace = b"/DeviceCMYK"
                        else:
                            colspace = b"/DeviceGray"

                        break
        except Exception:
            traceback.print_exc()
            raise ValueError("Couldn't process image: {}".format(self.image_name))

        bytes_.seek(0)
        image_data = bytes_.read()
        bytes_.seek(0)

        self.width = int(w)
        self.height = int(h)

        self.pdf_obj = {
            "Type": b"/XObject",
            "Subtype": b"/Image",
            "Width": self.width,
            "Height": self.height,
            "ColorSpace": colspace,
            "BitsPerComponent": int(depth),
            "Filter": b"/DCTDecode",
            "__skip_filter__": True,
            "__stream__": image_data,
        }

    def parse_png(self, bytes_: BinaryIO) -> None:
        """Method to convert a PNG image to a JPEG image and later parse it as
        a JPEG image.

        This method creates this instance's attibute ``pdf_obj``, containing
        a dict that can be added to a :class:`pdfme.base.PDFBase` instance as
        a PDF Stream object that represents this image.

        Args:
            bytes_ (BinaryIO): A file-like object containing the
                image.
        """
        from PIL import Image  # type: ignore

        im = Image.open(bytes_).convert("RGB")
        bytes_io = BytesIO()
        im.save(bytes_io, "JPEG")
        bytes_io.seek(0)
        self.parse_jpg(bytes_io)
        bytes_io.close()
        im.close()
