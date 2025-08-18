# ruff: noqa: C901

from __future__ import annotations

import csv
import dataclasses
import math
import re
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from typing import Self

from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews.misc import SeasonDay
from mmolb_utils.apis.cashews.stats_api import StatKey
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib import cached_ews
from mmolb_utils.lib.attributes import (
    ALL_ATTRIBUTES,
    Attribute,
)


@dataclasses.dataclass(frozen=True, slots=True)
class Interval:
    start: float = 0.0
    end: float = math.inf

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError(f"Impossible interval: {self}. {self.start} > {self.end}")

    @property
    def median(self) -> float:
        if math.isinf(self.start) and math.isinf(self.end):
            # the post-init checks guarantee that these are
            # negative and positive, respectively, so 0.0 is safe
            return 0.0
        if math.isinf(self.start) or math.isinf(self.end):
            raise ValueError(f"No median exists for infinite interval {self}")
        return (self.start + self.end) / 2

    @property
    def uncertainty(self) -> float:
        if math.isinf(self.start) or math.isinf(self.end):
            return math.inf
        return (self.end - self.start) / 2

    @property
    def value(self) -> str:
        return f"{self.median} ± {self.uncertainty}"

    def __iter__(self) -> Iterator[float]:
        yield self.start
        yield self.end

    def __str__(self) -> str:
        return f"[{self.start}, {self.end})"

    def __add__(self, other: object) -> Interval:
        if isinstance(other, float):
            other = Interval(other, other)
        if isinstance(other, Interval):
            return Interval(self.start + other.start, self.end + other.end)
        raise NotImplementedError

    def __sub__(self, other: object) -> Interval:
        if not isinstance(other, float | Interval):
            raise NotImplementedError
        return self + (-other)

    def __neg__(self) -> Interval:
        return Interval(-self.end, -self.start)

    def __and__(self, other: object) -> Interval:
        if not isinstance(other, Interval):
            raise NotImplementedError
        if self.end < other.start or other.end < self.start:
            raise ValueError(f"No intersection between {self} and {other}")
        return Interval(max(self.start, other.start), min(self.end, other.end))

    def __or__(self, other: object) -> Interval:
        if not isinstance(other, Interval):
            raise NotImplementedError
        return Interval(min(self.start, other.start), max(self.start, other.end))

    @classmethod
    def from_stars(cls, stars: str | int) -> Self:
        if isinstance(stars, str):
            stars = len(stars)
        stars *= 25
        return cls() & cls(stars - 12.5, stars + 12.5)


@dataclasses.dataclass
class PlayerVersion:
    chron_valid_from: datetime
    attributes: dict[Attribute, Interval] = dataclasses.field(default_factory=lambda: defaultdict(Interval))

    def update_from_talk(self, talk: dict[str, dict]) -> None:
        for group, group_talk in talk.items():
            for attribute, star in group_talk["stars"].items():
                try:
                    self.attributes[attribute] &= Interval.from_stars(star)
                except ValueError as e:
                    raise ValueError(f"Error with {attribute}: {e}") from e

    def update_from_birth(self, birth_season: int) -> None:
        if birth_season == 0:
            return
        if birth_season <= 2:
            interval = Interval(0, 100.0)
        else:
            interval = Interval(0, 106.5)  # what?
        for attribute in ALL_ATTRIBUTES:
            try:
                self.attributes[attribute] &= interval
            except ValueError as e:
                raise ValueError(f"Error with {attribute}: {e}") from e

    def as_json(self) -> dict:
        attributes = {attribute: str(self.attributes[attribute]) for attribute in ALL_ATTRIBUTES}
        return {
            "chron_valid_from": self.chron_valid_from,
            **attributes,
        }


augment_pattern = re.compile(r"(.+) gained \+(\d+?) (\w+?)\.")


def triangulate_attributes(player_id: EntityID) -> PlayerVersion:
    latest_player = cached_ews.get_entity(cashews.EntityKind.PlayerLite, player_id)
    latest_name = f"{latest_player['data']['FirstName']} {latest_player['data']['LastName']}"
    player = PlayerVersion(datetime.fromisoformat(latest_player["valid_from"]))
    feed = cached_ews.get_entity(cashews.EntityKind.PlayerFeed, player_id)["data"]["feed"]

    player.update_from_talk(latest_player["data"].get("Talk", {}))

    boosts: dict[Attribute, float] = defaultdict(float)

    for event in reversed(feed):
        if event["type"] != "augment":
            continue
        if "was Recomposed" in event["text"]:
            break

        augment_match = augment_pattern.match(event["text"])
        if augment_match is None:
            continue

        name, bonus, attribute = augment_match.groups()

        if name != latest_name:
            break

        player.attributes[attribute] -= float(bonus)
        boosts[attribute] += float(bonus)

        timestamp = datetime.fromisoformat(event["ts"])

        if timestamp <= SeasonDay(4, 120).timestamp:
            continue

        # print(event)

        new_talk = cached_ews.get_entity(cashews.EntityKind.Talk, player_id, at=timestamp)
        player.update_from_talk(new_talk["data"])

    if latest_player["data"]["Birthseason"] <= 1:
        # in early S1, megas and teamwides didn't have links and didn't end up in the player feed
        old_player = cached_ews.get_entity(cashews.EntityKind.PlayerLite, player_id, at=SeasonDay(2, 1).timestamp)
        if old_player is not None:
            old_name = f"{old_player['data']['FirstName']} {old_player['data']['LastName']}"
            team_feed_data = cached_ews.get_entity(cashews.EntityKind.TeamFeed, old_player["data"]["TeamID"])

            if team_feed_data is not None:
                team_feed = team_feed_data["data"]["feed"]

                player_aug_pattern = re.compile(old_name + r" gained \+(\d+?) (\w+?)\.")

                for event in reversed(team_feed):
                    if event["type"] != "augment":
                        continue
                    if event["links"]:
                        continue

                    augment_match = player_aug_pattern.match(event["text"])
                    if augment_match is None:
                        continue

                    bonus, attribute = augment_match.groups()
                    player.attributes[attribute] -= float(bonus)
                    boosts[attribute] += float(bonus)

    player.update_from_birth(latest_player["data"]["Birthseason"])

    for attribute, boost in boosts.items():
        player.attributes[attribute] += boost

    # for attribute, interval in player.attributes.items():
    #     print(f"{attribute:13} {str(interval):16} {interval.value}")

    return player


# triangulate_attributes("6842fa8608b7fc5e21e8b1e9")

RED = "\033[31m"
RESET = "\033[0m"

players_to_check = ["68412a41e2d7557e153cc723"]


def all_players():
    # set_print_progress(False)

    results: dict[tuple[str, str], PlayerVersion] = {}
    errors: dict[tuple[str, str], str] = {}

    players = list(
        player
        for player in cashews.get_stats(StatKey.Appearances, StatKey.PlateAppearances, season=4, names=True)
        if player["appearances"] or player["plate_appearances"]
        # if player["player_id"] in players_to_check
    )

    cached_ews.set_ids(tuple(player["player_id"] for player in players))

    for i, row in enumerate(players):
        player_name = row["player_name"]
        player_id = row["player_id"]

        output = f"{i + 1:5}/{len(players)} https://mmolb.com/player/{player_id} {player_name}"

        try:
            results[player_id, player_name] = triangulate_attributes(player_id)
        except Exception as e:
            errors[player_id, player_name] = str(e)
            output = f"{RED}{output} {e}{RESET}"
            # raise

        print(output)

    print(f"{len(errors)} Errors: {errors}")

    with open("output.csv", "w", newline="") as csvfile:
        fieldnames = ["player_id", "chron_valid_from", *ALL_ATTRIBUTES]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for (player_id, _), version in results.items():
            writer.writerow({"player_id": player_id, **version.as_json()})


# cached_ews.get_entity(cashews.EntityKind.Season, "")
# all_players()
# set_print_progress(False)
# cached_ews.set_use_cache(False)
all_players()
# # print(triangulate_attributes("684767f9c700d5fd9a78c7a9"))
