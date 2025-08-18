import functools
import struct
from datetime import UTC, datetime

from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews.misc import SeasonDay


@functools.lru_cache
def timestamps() -> dict[SeasonDay, datetime]:
    times: dict[SeasonDay, datetime] = {}
    for season in cashews.get_entities(cashews.EntityKind.Season):
        for day in cashews.get_entities(cashews.EntityKind.Day, id=season["data"]["Days"]):
            if not day["data"]["Games"]:
                continue

            game = next((game for game in day["data"]["Games"] if game["State"] != "Scheduled"), None)
            if game is None:
                continue
            try:
                id = bytes.fromhex(day["data"]["Games"][0]["GameID"])
            except Exception:
                print(day["data"]["Games"][0])
                raise
            timestamp, _ = struct.unpack(">iq", id)
            times[SeasonDay(day["data"]["Season"], day["data"]["Day"])] = datetime.fromtimestamp(timestamp, UTC)
    return times
