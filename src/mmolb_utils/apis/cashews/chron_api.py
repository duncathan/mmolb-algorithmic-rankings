from __future__ import annotations

import itertools
import typing
from collections.abc import Iterator, Mapping
from datetime import datetime
from enum import Enum
from typing import Literal, ReadOnly, TypedDict

from mmolb_utils.apis.cashews.misc import SnakeCaseParam
from mmolb_utils.apis.cashews.request import _get_paginated_data

if typing.TYPE_CHECKING:
    from mmolb_utils.apis.cashews.misc import SortOrder
    from mmolb_utils.apis.cashews.request import Param
    from mmolb_utils.apis.mmolb import EntityID
    from mmolb_utils.lib.attributes import (
        BaserunningAttribute,
        BattingAttribute,
        CategoryTalk,
        ClubhouseTalk,
        DefenseAttribute,
        PitchingAttribute,
    )

type IsoDateTime = datetime


class EntityVersion[T: Mapping = dict](TypedDict):
    kind: str
    """Always a valid `EntityKind` value"""

    entity_id: EntityID
    valid_from: IsoDateTime
    valid_to: IsoDateTime | None
    data: ReadOnly[T]


class EntityKind(SnakeCaseParam, Enum):
    State = 1
    League = 2
    Team = 3
    Player = 4
    Game = 5

    Time = 6
    Nouns = 7
    Adjectives = 8

    PlayerLite = 9
    TeamLite = 10

    News = 11
    Spotlight = 12
    Election = 13

    GamesEndpoint = 14
    PostseasonBracket = 15
    Message = 16

    Schedule = 17
    """*Deprecated*"""

    Season = 18
    Day = 19
    PatchNotes = 20

    Talk = 21
    TalkBatting = 22
    TalkPitching = 23
    TalkBaserunning = 24
    TalkDefense = 25

    SuperstarGames = 26

    PlayerFeed = 27
    TeamFeed = 28


type AnyCategoryTalk = Literal[
    EntityKind.TalkBatting, EntityKind.TalkBaserunning, EntityKind.TalkPitching, EntityKind.TalkDefense
]


def _split_ids(id: EntityID | list[EntityID] | None = None) -> Iterator[Param]:
    if not isinstance(id, list):
        yield id
        return

    yield from itertools.batched(id, 1000)


@typing.overload
def get_entities(
    kind: Literal[EntityKind.Talk],
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[ClubhouseTalk]]: ...


@typing.overload
def get_entities(  # type: ignore[overload-overlap]
    kind: Literal[EntityKind.TalkBatting],
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[CategoryTalk[BattingAttribute]]]: ...


@typing.overload
def get_entities(  # type: ignore[overload-overlap]
    kind: Literal[EntityKind.TalkBaserunning],
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[CategoryTalk[BaserunningAttribute]]]: ...


@typing.overload
def get_entities(  # type: ignore[overload-overlap]
    kind: Literal[EntityKind.TalkPitching],
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[CategoryTalk[PitchingAttribute]]]: ...


@typing.overload
def get_entities(  # type: ignore[overload-overlap]
    kind: Literal[EntityKind.TalkDefense],
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[CategoryTalk[DefenseAttribute]]]: ...


@typing.overload
def get_entities(
    kind: AnyCategoryTalk,
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[CategoryTalk]]: ...


def get_entities(
    kind: EntityKind,
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[dict]]:
    for ids in _split_ids(id):
        yield from _get_paginated_data(
            "chron/v0/entities",
            kind.name,
            EntityVersion,
            kind=kind,
            at=at,
            id=ids,
            order=order,
            count=count,
        )


def get_versions(
    kind: EntityKind,
    before: IsoDateTime | None = None,
    after: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[dict]]:
    for ids in _split_ids(id):
        yield from _get_paginated_data(
            "chron/v0/versions",
            kind.name,
            EntityVersion,
            kind=kind,
            before=before,
            after=after,
            id=ids,
            order=order,
            count=count,
        )
