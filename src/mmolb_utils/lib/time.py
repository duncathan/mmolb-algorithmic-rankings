import functools
import itertools
import struct
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Final, Literal, NamedTuple, Self

from tqdm import tqdm

from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews.request import suppress_prints
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib import cached_ews

type SpecialDay = Literal[
    "Preseason",
    "Superstar Day 1",
    "Superstar Day 2",
    "Postseason Preview",
    "Election",
    "Holiday",
    "Special Event",
    "Event",
]

INTERPOLATED_DAYS: Final[dict[SpecialDay, float]] = {
    "Preseason": 0,
    "Superstar Day 1": 120.1,
    "Superstar Day 2": 120.2,
    "Election": 300,
    "Holiday": 301,
    "Special Event": 1,
    "Event": 1,
}


class SeasonDay(NamedTuple):
    season: int
    day: int | SpecialDay

    @property
    def url_param(self) -> str:
        return f"{self.season},{self.day}"

    @property
    def timestamp(self) -> datetime:
        from mmolb_utils.lib.time import timestamps

        return timestamps()[self]

    @classmethod
    def from_timestamp(cls, timestamp: datetime | None) -> Self:
        if timestamp is None:
            return cls(today().season, today().day)
        for today_, tomorrow in itertools.pairwise(sorted(timestamps().keys())):
            if today_.timestamp <= timestamp < tomorrow.timestamp:
                return cls(today_.season, today_.day)
        return cls(tomorrow.season, tomorrow.day)

    @property
    def _day_value(self) -> float:
        if isinstance(self.day, int):
            return self.day
        return INTERPOLATED_DAYS[self.day]

    def __gt__(self, other: object) -> bool:
        return (self.season, self._day_value) > other

    def __lt__(self, other: object) -> bool:
        return (self.season, self._day_value) < other

    def __ge__(self, other: object) -> bool:
        return (self.season, self._day_value) >= other

    def __le__(self, other: object) -> bool:
        return (self.season, self._day_value) <= other

    def __eq__(self, other: object) -> bool:
        return (self.season, self._day_value) == other

    def __ne__(self, other: object) -> bool:
        return (self.season, self._day_value) != other


def timestamp_from_entity_id(entity_id: EntityID) -> datetime:
    id = bytes.fromhex(entity_id)
    timestamp, _ = struct.unpack(">iq", id)
    return datetime.fromtimestamp(timestamp, UTC)


@functools.lru_cache
def timestamps() -> dict[SeasonDay, datetime]:
    times: dict[SeasonDay, datetime] = {}
    with suppress_prints():
        for season in tqdm(
            list(cached_ews.all_entities(cashews.EntityKind.Season)), leave=False, desc="Generating timestamps"
        ):
            days = season["data"]["Days"]
            days.append(season["data"]["SuperstarDay1"])
            days.append(season["data"]["SuperstarDay2"])
            for day in tqdm(
                list(cached_ews.all_entities(cashews.EntityKind.Day, id=days)),
                leave=False,
                desc=f"Season {season['data']['Season']}",
            ):
                if not day["data"]["Games"]:
                    continue

                game = next((game for game in day["data"]["Games"] if game["State"] != "Scheduled"), None)
                if game is None:
                    continue
                timestamp = timestamp_from_entity_id(day["data"]["Games"][0]["GameID"])
                times[SeasonDay(day["data"]["Season"], day["data"]["Day"])] = timestamp
    return times


def timestamp_range(start: SeasonDay, end: SeasonDay, *, reverse: bool = False) -> Iterator[SeasonDay]:
    for season_day in sorted(timestamps().keys(), reverse=reverse):
        if start <= season_day < end:
            yield season_day


def today() -> SeasonDay:
    return max(timestamps().keys())
