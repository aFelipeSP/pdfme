from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, Union


Number = Union[float, int]
DictStr = Dict[str, Any]
MarginType = Union[int, float, Iterable[Number], dict]
PageType = Union[Number, str, Iterable[Number]]
ColorType = Union[int, float, str, list, tuple]
ImageType = Union[str, Path, BytesIO]
TextType = Union[str, list, tuple, dict]
