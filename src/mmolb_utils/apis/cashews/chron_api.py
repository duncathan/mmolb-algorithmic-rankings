import itertools
from collections.abc import Iterator
from enum import Enum
from typing import TypedDict

from mmolb_utils.apis.cashews.misc import SnakeCaseParam, SortOrder
from mmolb_utils.apis.cashews.request import Param, _get_paginated_data
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.json_lib import JsonType

type IsoDateTime = str


class EntityVersion[T: JsonType = JsonType](TypedDict):
    kind: str
    """Always a valid `EntityKind` value"""

    entity_id: EntityID
    valid_from: IsoDateTime
    valid_to: IsoDateTime | None
    data: T


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


def _split_ids(id: EntityID | list[EntityID] | None = None) -> Iterator[Param]:
    if not isinstance(id, list):
        yield id
        return

    yield from itertools.batched(id, 1000)


def get_entities[T: JsonType = JsonType](
    kind: EntityKind,
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[T]]:
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


def get_versions[T: JsonType = JsonType](
    kind: EntityKind,
    before: IsoDateTime | None = None,
    after: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion[T]]:
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
