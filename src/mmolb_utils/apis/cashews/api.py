from collections.abc import Iterable, Iterator

import requests
from caseconverter import snakecase

from mmolb_utils.apis.cashews.types import (
    CashewsGame,
    CashewsLeague,
    CashewsLocation,
    CashewsPlayerStats,
    CashewsScorigami,
    CashewsTeam,
    EntityKind,
    EntityVersion,
    GroupColumn,
    IsoDateTime,
    PaginatedResult,
    SeasonDay,
    SortOrder,
    StatKey,
)
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.json_lib import JsonObject, JsonType

CASHEWS_API = "https://freecashe.ws/api"


FirstPage = object()

_print_progress = True


def _get_simple_data(url: str) -> JsonType:
    # print(url)
    response = requests.get(url)

    if response.status_code == 500:
        raise requests.HTTPError(f"500 Server Error: '{response.text}'", response=response)

    response.raise_for_status()  # handle other errors

    return response.json()


def _get_paginated_data[T: JsonType = JsonType](base_url: str, name: str | None = None) -> Iterator[T]:
    global _print_progress

    page_num = 0
    next_page = FirstPage
    url = base_url

    while next_page is not None:
        page_num += 1

        if next_page is not FirstPage:
            url = f"{base_url}&page={next_page}"

        data: PaginatedResult[T] | list[T] = _get_simple_data(url)

        if _print_progress:
            if name is None:
                print(f"Page {page_num}")
            else:
                print(f"{name}: page {page_num}")

        if isinstance(data, list):
            yield from data
            break

        next_page = data["next_page"]
        yield from data["items"]

    if _print_progress:
        print()


def get_entities(
    kind: EntityKind,
    at: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion]:
    url = f"{CASHEWS_API}/chron/v0/entities?kind={snakecase(kind.name)}&order={order}&count={count}"

    if at is not None:
        url += f"&at={at}"

    if id:
        if isinstance(id, list):
            url += f"&id={','.join(id)}"
        else:
            url += f"&id={id}"

    yield from _get_paginated_data(url, kind.name)


def get_versions(
    kind: EntityKind,
    before: IsoDateTime | None = None,
    after: IsoDateTime | None = None,
    id: EntityID | list[EntityID] | None = None,
    order: SortOrder = "asc",
    count: int = 1000,
) -> Iterator[EntityVersion]:
    url = f"{CASHEWS_API}/chron/v0/versions?kind={snakecase(kind.name)}&order={order}&count={count}"

    if before is not None:
        url += f"&before={before}"

    if after is not None:
        url += f"&after={after}"

    if id:
        if isinstance(id, list):
            url += f"&id={','.join(id)}"
        else:
            url += f"&id={id}"

    yield from _get_paginated_data(url, "Versions")


def get_games(
    season: int, day: int | None = None, team: EntityID | None = None, order: SortOrder = "asc", count: int = 1000
) -> Iterator[CashewsGame]:
    url = f"{CASHEWS_API}/games?season={season}&order={order}&count={count}"

    if day is not None:
        url += f"&day={day}"

    if team is not None:
        url += f"&team={team}"

    yield from _get_paginated_data(url, "Games")


def get_teams() -> Iterator[CashewsTeam]:
    yield from _get_paginated_data(f"{CASHEWS_API}/teams", "Teams")


def get_leagues() -> Iterator[CashewsLeague]:
    yield from _get_paginated_data(f"{CASHEWS_API}/leagues", "Leagues")


def get_player_stats(
    start: SeasonDay | None = None,
    end: SeasonDay | None = None,
    player: EntityID | None = None,
    team: EntityID | None = None,
) -> Iterator[CashewsPlayerStats]:
    url = f"{CASHEWS_API}/player-stats?"

    if player is not None:
        url += f"&player={player}"
    if team is not None:
        url += f"&team={team}"
    if start is not None:
        url += f"&start={start.url_param}"
    if end is not None:
        url += f"&end={end.url_param}"

    yield from _get_paginated_data(url, "Player Stats")


def get_scorigami() -> Iterator[CashewsScorigami]:
    yield from _get_paginated_data(f"{CASHEWS_API}/scorigami", "Scorigami")


def get_locations() -> Iterator[CashewsLocation]:
    yield from _get_paginated_data(f"{CASHEWS_API}/locations", "Locations")


def get_stats(  # noqa: C901
    *fields: StatKey,
    group: GroupColumn | Iterable[GroupColumn] = GroupColumn.Player,
    start: SeasonDay | None = None,
    end: SeasonDay | None = None,
    season: int | None = None,
    player: EntityID | None = None,
    team: EntityID | None = None,
    league: EntityID | None = None,
    game: EntityID | None = None,
    sort: StatKey | None = None,
    count: int | None = None,
    filter_by: str | None = None,
    names: bool = False,
) -> list[JsonObject]:
    url = f"{CASHEWS_API}/stats?format=json&fields={','.join(snakecase(field.name) for field in fields)}"

    if isinstance(group, GroupColumn):
        group = [group]
    if group:
        url += f"&group={','.join(snakecase(field.name) for field in group)}"

    if start is not None:
        url += f"&start={start.url_param}"
    if end is not None:
        url += f"&end={end.url_param}"

    if season is not None:
        url += f"&season={season}"

    if player is not None:
        url += f"&player={player}"
    if team is not None:
        url += f"&team={team}"
    if league is not None:
        url += f"&league={league}"
    if game is not None:
        url += f"&game={game}"

    if sort is not None:
        url += f"&sort={snakecase(sort)}"
    if count is not None:
        url += f"&count={count}"
    if filter_by is not None:
        url += filter_by
    url += f"&names={str(names).lower()}"

    return _get_simple_data(url)
