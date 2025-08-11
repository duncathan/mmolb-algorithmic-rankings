from enum import Enum
from typing import Literal, NamedTuple

from caseconverter import snakecase

type SortOrder = Literal["asc", "desc"]


class SeasonDay(NamedTuple):
    season: int
    day: int

    @property
    def url_param(self) -> str:
        return f"{self.season},{self.day}"


class SnakeCaseParam:
    @property
    def url_param(self) -> str:
        assert isinstance(self, Enum)
        return snakecase(self.name)
