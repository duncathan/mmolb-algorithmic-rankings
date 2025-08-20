from collections.abc import Iterator

from mmolb_utils.apis.cashews.misc import SortOrder
from mmolb_utils.apis.cashews.request import _get_paginated_data
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.json_lib import JsonObject
from mmolb_utils.lib.time import SeasonDay

CashewsGame = JsonObject  # TODO: TypedDict


def get_games(
    season: int, day: int | None = None, team: EntityID | None = None, order: SortOrder = "asc", count: int = 1000
) -> Iterator[CashewsGame]:
    yield from _get_paginated_data(
        "games",
        "Games",
        CashewsGame,
        season=season,
        day=day,
        team=team,
        order=order,
        count=count,
    )


CashewsTeam = JsonObject  # TODO: TypedDict


def get_teams() -> Iterator[CashewsTeam]:
    yield from _get_paginated_data("teams", "Teams", CashewsTeam)


CashewsLeague = JsonObject  # TODO: TypedDict


def get_leagues() -> Iterator[CashewsLeague]:
    yield from _get_paginated_data("leagues", "Leagues", CashewsLeague)


CashewsPlayerStats = JsonObject  # TODO: TypedDict


def get_player_stats(
    start: SeasonDay | None = None,
    end: SeasonDay | None = None,
    player: EntityID | None = None,
    team: EntityID | None = None,
) -> Iterator[CashewsPlayerStats]:
    yield from _get_paginated_data(
        "player-stats",
        "Player Stats",
        CashewsPlayerStats,
        start=start,
        end=end,
        player=player,
        team=team,
    )


CashewsScorigami = JsonObject  # TODO: TypedDict


def get_scorigami() -> Iterator[CashewsScorigami]:
    yield from _get_paginated_data("scorigami", "Scorigami", CashewsScorigami)


CashewsLocation = JsonObject  # TODO: TypedDict


def get_locations() -> Iterator[CashewsLocation]:
    yield from _get_paginated_data("locations", "Locations", CashewsLocation)
