from io import BytesIO
from typing import Tuple, Dict, Union

ConverterService = Tuple[Union[BytesIO, str], bool]
ConverterHandler = Tuple[str, Dict[str, str]]
