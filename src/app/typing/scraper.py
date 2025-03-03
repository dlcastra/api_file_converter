from typing import TypeAlias, Tuple, Union, List, Dict

ScraperService: TypeAlias = Tuple[Union[str, List[str]], bool]
ScraperHandler: TypeAlias = Tuple[str, Dict[str, Union[int, str]]]
EmptyListOrListStr: TypeAlias = Union[List, List[str]]
