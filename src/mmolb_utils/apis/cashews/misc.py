from enum import Enum
from typing import Literal

from caseconverter import snakecase

type SortOrder = Literal["asc", "desc"]


class SnakeCaseParam:
    @property
    def url_param(self) -> str:
        assert isinstance(self, Enum)
        return snakecase(self.name)
