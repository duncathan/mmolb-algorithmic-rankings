import functools
import typing

from mmolb_utils.apis import mmolb

ANDROMEDA = "686dcf38775d6c67e270a938"
MILKY_WAY = "686dcf83cd624ef8ea0f6abc"


@functools.lru_cache
def players_in_duel() -> set[str]:
    players: set[str] = set()

    for team_id in (ANDROMEDA, MILKY_WAY):
        team = mmolb.get_team_feed(team_id)
        print(team.keys())

        for feed in team["feed"]:
            for link in feed["links"]:
                if link["type"] == "player":
                    players.add(typing.cast("str", link["id"]))
    return players
