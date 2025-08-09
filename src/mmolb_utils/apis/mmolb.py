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


def get_player_feed(id: str) -> JsonType:
    url = f"{MMOLB_API}/feed?player={id}"
    return get_data(url)

def get_team_feed(id: str) -> JsonType:
    url = f"{MMOLB_API}/feed?team={id}"
    return get_data(url)


def get_players(*player_ids: str) -> Iterator[JsonObject]:
    players = [id for id in player_ids if (id and id != "#")]
    if not players:
        yield from ()
        return
    
    num_pages = (len(players) // 100) + 1
    for i in range(num_pages):
        print(f"players page {i} / {num_pages}")
        page = players[i*100:(i+1) * 100]
        url = f"{MMOLB_API}/players?ids={','.join(page)}"
        yield from get_data(url)['players']
