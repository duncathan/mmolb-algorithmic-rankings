# ruff: noqa: C901

from __future__ import annotations

import csv
import dataclasses
import functools
import math
import re
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Self

from colorama import Fore
from frozendict import frozendict
from tqdm import tqdm

from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews.stats_api import StatKey
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib import cached_ews
from mmolb_utils.lib.attributes import (
    ALL_ATTRIBUTES,
    Attribute,
)
from mmolb_utils.lib.io import safe_write
from mmolb_utils.lib.time import SeasonDay, timestamp_range


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


def attribute_dict() -> dict[Attribute, Interval]:
    return defaultdict(Interval)


class PlayerError(ValueError):
    def __init__(self, *args: object, player_id: EntityID, player_name: str) -> None:
        self.player_id = player_id
        self.player_name = player_name
        super().__init__(*args)


@dataclasses.dataclass
class PlayerHistory:
    player_id: EntityID
    working_name: str = ""
    working_attributes: dict[Attribute, Interval] = dataclasses.field(default_factory=attribute_dict)
    recomps: list[PlayerComposition] = dataclasses.field(default_factory=list)
    bonus_history: dict[datetime, list[tuple[Attribute, float]]] = dataclasses.field(
        default_factory=lambda: defaultdict(list)
    )

    def _update_attributes(
        self,
        attributes: dict[Attribute, Interval],
        name: str | None = None,
    ) -> None:
        for attribute, interval in attributes.items():
            try:
                self.working_attributes[attribute] &= interval
            except ValueError as e:
                raise PlayerError(
                    f"Error with {attribute}: {e}",
                    player_id=self.player_id,
                    player_name=name or self.working_name,
                ) from e

    def update_from_talk(self, talk: dict[str, dict]) -> None:
        attributes: dict[Attribute, Interval] = {}
        for _, group_talk in talk.items():
            for attribute, star in group_talk["stars"].items():
                attributes[attribute] = Interval.from_stars(star)
        self._update_attributes(attributes)

    def update_from_birth(self, birthdate: datetime, name: str | None = None) -> None:
        if birthdate < SeasonDay(1, 1).timestamp:
            return

        interval = Interval(0, 106.5)  # what?
        attributes = {attribute: interval for attribute in ALL_ATTRIBUTES}
        self._update_attributes(attributes, name)

    def add_bonus(self, timestamp: datetime, attribute: Attribute, bonus: float) -> None:
        self.working_attributes[attribute] -= bonus
        self.bonus_history[timestamp].append((attribute, bonus))

    def save_composition(self, birth: datetime | None, name: str) -> None:
        if self.recomps:
            death = self.recomps[-1].lifetime[0]
        else:
            death = None

        if birth is None:
            player = cached_ews.get_earliest(cashews.EntityKind.PlayerLite, self.player_id)
            birth = datetime.fromisoformat(player["valid_from"])

        self.update_from_birth(birth, name)

        bonuses = frozendict(
            {
                time: tuple(bonuses)
                for time, bonuses in self.bonus_history.items()
                if (birth < time) and ((death is None) or time <= death)
            }
        )
        recomp = PlayerComposition(
            player_id=self.player_id,
            player_name=name,
            lifetime=(birth, death),
            initial_attributes=frozendict(
                {attribute: self.working_attributes[attribute] for attribute in ALL_ATTRIBUTES}
            ),
            bonus_history=bonuses,
        )
        self.recomps.append(recomp)
        self.working_attributes = attribute_dict()

    def get_composition(self, timestamp: datetime | None = None) -> PlayerComposition:
        if timestamp is None:
            return next(comp for comp in self.recomps if comp.lifetime[1] is None)
        for comp in self.recomps:
            birth, death = comp.lifetime
            if (birth < timestamp) and ((death is None) or death > timestamp):
                return comp
        raise ValueError(f"No composition exists at {timestamp}")

    def all_versions(self) -> Iterator[PlayerSnapshot]:
        for comp in self.recomps:
            yield from comp.all_versions()


@dataclasses.dataclass(frozen=True)
class PlayerComposition:
    player_id: EntityID
    player_name: str
    lifetime: tuple[datetime, datetime | None]
    initial_attributes: frozendict[Attribute, Interval]
    bonus_history: frozendict[datetime, tuple[tuple[Attribute, float], ...]]

    @functools.lru_cache
    def _get_snapshot(self, timestamp: datetime) -> PlayerSnapshot:
        birth, death = self.lifetime
        if timestamp < birth or ((death is not None) and timestamp > death):
            raise ValueError(f"Player {self.player_id} did not exist at {timestamp}")

        attributes = dict(self.initial_attributes)
        for bonus_time, bonuses in self.bonus_history.items():
            if birth < bonus_time <= timestamp:
                for attribute, bonus in bonuses:
                    attributes[attribute] += bonus

        player = cached_ews.get_entity(cashews.EntityKind.PlayerLite, self.player_id, timestamp)
        name = f"{player['data']['FirstName']} {player['data']['LastName']}"

        return PlayerSnapshot(
            player_id=self.player_id,
            player_name=name,
            # chron_valid_from=datetime.fromisoformat(player["valid_from"]),
            valid_from=None,
            valid_to=None,
            base_attributes=frozendict(attributes),
        )

    def get_snapshot_at(self, timestamp: datetime | SeasonDay) -> PlayerSnapshot:
        if isinstance(timestamp, SeasonDay):
            timestamp = timestamp.timestamp
        return self._get_snapshot(timestamp)

    def all_versions(self) -> Iterator[PlayerSnapshot]:
        start, finish = self.lifetime
        lifetimes: dict[PlayerSnapshot, set[datetime]] = defaultdict(set)
        for day in timestamp_range(SeasonDay.from_timestamp(start), SeasonDay.from_timestamp(finish)):
            if start <= day.timestamp:
                snapshot = self.get_snapshot_at(day)
                lifetimes[snapshot].add(day.timestamp)
        for snapshot, lifetime in lifetimes.items():
            yield dataclasses.replace(
                snapshot,
                valid_from=min(lifetime),
                valid_to=max(lifetime),
            )


@dataclasses.dataclass(frozen=True)
class PlayerSnapshot:
    player_id: EntityID
    player_name: str
    # chron_valid_from: datetime = dataclasses.field(hash=False)
    valid_from: datetime | None
    valid_to: datetime | None
    base_attributes: frozendict[Attribute, Interval]

    @functools.cached_property
    def as_json(self) -> frozendict:
        attributes = {attribute: str(self.base_attributes[attribute]) for attribute in ALL_ATTRIBUTES}
        return frozendict(
            {
                "player_id": self.player_id,
                "player_name": self.player_name,
                "valid_from": self.valid_from,
                "valid_to": self.valid_to,
                **attributes,
            }
        )


OVERWRITTEN_RECOMPS = {
    "68414353f7b5d3bf791d6af7": {14},
    "6850da687db123b15516c542": {12},
    "684104c708b7fc5e21e8ab83": {15},
    "68413fd1183c892d88a10074": {22},
    "6845d8ba88056169e0079081": {14},
    "68751e24d9c3888e3e26a328": {1},
    "6841030dec9dc637cfd0cade": {16},
    "6840fcd8ed58166c1895a9a5": {14},
    "6840fa88896f631e9d688d28": {18},
    "684674e9ec9dc637cfd0d407": {11},
    "6840faf7e63d9bb8728896c0": {12},
    "6805db0cac48194de3cd405f": {6},
    "68751f7fc1f9dc22d3a8f267": {7},
}


augment_pattern = re.compile(r"^(?:.*?! )?(.+) gained \+(\d+?) (\w+?)[ .]")
recomp_pattern = re.compile(r"(.+?) was Recomposed (?:into|using) (.+?)\.")


def triangulate_attributes(player_id: EntityID) -> PlayerHistory:
    player = PlayerHistory(player_id)

    latest_player = cached_ews.get_entity(cashews.EntityKind.PlayerLite, player_id)
    if latest_player is None:
        return player

    player.working_name = f"{latest_player['data']['FirstName']} {latest_player['data']['LastName']}"

    feed_data = cached_ews.get_entity(cashews.EntityKind.PlayerFeed, player_id)
    feed = feed_data["data"]["feed"]

    latest_talk = cached_ews.get_entity(cashews.EntityKind.Talk, player_id)
    if latest_talk is None:
        return player
    player.update_from_talk(latest_talk["data"])

    for i, event in reversed(list(enumerate(feed))):
        timestamp = datetime.fromisoformat(event["ts"])
        if timestamp > datetime.fromisoformat(latest_talk["valid_from"]):
            continue

        recomp_match = recomp_pattern.match(event["text"])
        if recomp_match is not None:
            player.working_name, new_name = recomp_match.groups()
            player.save_composition(timestamp, new_name)
            continue

        augment_match = augment_pattern.match(event["text"])
        if augment_match is None:
            continue

        name, bonus, attribute = augment_match.groups()

        if (name != player.working_name) and (i not in OVERWRITTEN_RECOMPS.get(player_id, set())):
            player.save_composition(timestamp, player.working_name)
            player.working_name = name

        player.add_bonus(timestamp, attribute, float(bonus))

        if timestamp <= SeasonDay(4, 120).timestamp:
            continue

        new_talk = cached_ews.get_entity(cashews.EntityKind.Talk, player_id, at=timestamp)
        if new_talk is not None:
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
                    if any(link["id"] == player_id for link in event["links"]):
                        continue

                    timestamp = datetime.fromisoformat(event["ts"])

                    augment_match = player_aug_pattern.match(event["text"])
                    if augment_match is None:
                        continue

                    bonus, attribute = augment_match.groups()
                    bonus = float(bonus)
                    if bonus != 50:
                        player.add_bonus(timestamp, attribute, bonus)

    player.save_composition(None, player.working_name)

    return player


def all_players(out_path: Path | None):
    results: list[PlayerHistory] = []
    errors: list[PlayerError] = []

    players = list(
        player
        for player in cashews.get_stats(StatKey.Appearances, StatKey.PlateAppearances)
        if player["appearances"] or player["plate_appearances"]
    )

    cached_ews.set_ids(tuple(player["player_id"] for player in players))

    for row in tqdm(players, desc="Triangulating attributes"):
        player_id = row["player_id"]

        try:
            results.append(triangulate_attributes(player_id))
        except PlayerError as e:
            errors.append(e)
        except Exception as e:
            raise e.__class__(f"https://mmolb.com/player/{player_id}: {e}") from e

    if errors:
        tqdm.write(f"{Fore.RED}{len(errors)} errors:{Fore.RESET}")
        name_len = max(len(e.player_name) for e in errors)
        for error in errors:
            url = f"https://mmolb.com/player/{error.player_id}"
            name = f"{error.player_name:{name_len}}"
            message = f"{Fore.RED}{error}{Fore.RESET}"
            tqdm.write(f"    {url} {name} {message}")
    else:
        tqdm.write(f"{Fore.GREEN}No errors!{Fore.RESET}")

    if out_path is None:
        return

    with safe_write(out_path, newline="", encoding="utf_8_sig") as csvfile:
        fieldnames = ["player_id", "player_name", "chron_valid_from", "valid_from", "valid_to", *ALL_ATTRIBUTES]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for history in tqdm(results, desc="Saving output file"):
            for version in history.all_versions():
                writer.writerow(version.as_json)


if __name__ == "__main__":
    all_players(Path("output.csv"))
    # all_players(None)
