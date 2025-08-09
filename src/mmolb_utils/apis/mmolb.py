import typing
from collections.abc import Iterator

import requests

from mmolb_utils.lib.json_lib import JsonObject, JsonType

type EntityID = str

MMOLB_API = "https://mmolb.com/api"


def get_data(url: str) -> JsonType:
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_simple_endpoint(endpoint: str, id: str) -> JsonType:
    url = f"{MMOLB_API}/{endpoint}/{id}"
    return get_data(url)


class FeedEntry(typing.TypedDict):
    day: int
    emoji: str
    links: list[JsonObject]
    season: int
    status: str
    text: str
    ts: str
    type: str


class Feed(typing.TypedDict):
    feed: list[FeedEntry]


def get_player_feed(id: str) -> Feed:
    url = f"{MMOLB_API}/feed?player={id}"
    return typing.cast("Feed", get_data(url))


def get_team_feed(id: str) -> Feed:
    url = f"{MMOLB_API}/feed?team={id}"
    return typing.cast("Feed", get_data(url))


def get_players(*player_ids: str) -> Iterator[JsonObject]:
    player_ids = tuple(id for id in player_ids if (id and id != "#"))
    if not player_ids:
        yield from ()
        return

    num_pages = (len(player_ids) // 100) + 1
    for i in range(num_pages):
        print(f"players page {i} / {num_pages}")
        page = player_ids[i * 100 : (i + 1) * 100]
        url = f"{MMOLB_API}/players?ids={','.join(page)}"
        data = typing.cast("dict[str, list[JsonObject]]", get_data(url))
        yield from data["players"]
