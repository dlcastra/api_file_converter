from typing import TypeAlias, Tuple, Union

ConverterService: TypeAlias = Tuple[str, bool]
ConverterHandler = Union[Tuple[str, str], Tuple[str, dict]]
