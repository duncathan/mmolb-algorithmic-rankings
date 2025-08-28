from collections.abc import Iterable
from enum import Enum
from typing import Literal, TypeGuard

from caseconverter import snakecase

type SortOrder = Literal["asc", "desc"]


class SnakeCaseParam:
    @property
    def url_param(self) -> str:
        assert isinstance(self, Enum)
        return snakecase(self.name)


def is_coherent_iterable[T](value: object, type_: type[T]) -> TypeGuard[Iterable[T]]:
    if not isinstance(value, Iterable):
        return False
    return all(isinstance(subvalue, type_) for subvalue in value)
