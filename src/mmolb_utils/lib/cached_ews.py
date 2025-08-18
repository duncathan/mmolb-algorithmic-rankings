import functools
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta

import platformdirs

from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews.request import suppress_prints
from mmolb_utils.apis.mmolb import EntityID

_perform_cacheing = True


def set_use_cache(value: bool) -> None:
    global _perform_cacheing
    _perform_cacheing = value


_ids = ()


def set_ids(value: tuple[EntityID, ...]) -> None:
    global _ids
    _ids = value


@functools.lru_cache
def _cached_entities(kind: cashews.EntityKind, ids: tuple[EntityID, ...]) -> dict[EntityID, list[dict]]:
    print(f"Loading {kind.name}...")
    cache = platformdirs.user_cache_path("mmolb_utils")
    cache.mkdir(parents=True, exist_ok=True)
    local_file = cache.joinpath(f"{kind.url_param}.json")

    timestamp = datetime.now(UTC)
    entities = defaultdict(list)

    id = list(ids) if ids else None

    try:
        with local_file.open("r") as file:
            previous = json.load(file)
            after = datetime.fromisoformat(previous["timestamp"])
            entities.update(previous["entities"])
            if timestamp - after < timedelta(hours=1):
                return entities

    except (json.JSONDecodeError, FileNotFoundError):
        after = None

    print(f"Updating {kind.name}...")
    with suppress_prints():
        if kind in {cashews.EntityKind.PlayerFeed, cashews.EntityKind.TeamFeed}:
            entities = defaultdict(list)
            for entity in cashews.get_entities(kind, id=id, order="desc"):
                entities[entity["entity_id"]].append(entity)
        else:
            for entity in cashews.get_versions(kind, id=id, order="desc", after=after):
                entities[entity["entity_id"]].append(entity)

    print(f"Saving {kind.name}...")
    with local_file.open("w") as file:
        json.dump(
            {
                "timestamp": timestamp.isoformat(),
                "entities": entities,
            },
            file,
            indent=1,
        )

    return entities


def get_entity(kind: cashews.EntityKind, entity_id: EntityID, at: datetime | None = None) -> dict | None:
    if not _perform_cacheing:
        return next(cashews.get_entities(kind, id=entity_id, at=at), None)
    entities = _cached_entities(kind, _ids)
    versions = entities[entity_id]
    if not versions:
        return None
    if at is None:
        at = datetime.now(UTC)
    return next(
        (version for version in versions if datetime.fromisoformat(version["valid_from"]) < at),
        versions[-1],
    )


# def get_player(player_id: EntityID, at: datetime | None = None) -> dict:
#     return _get_entity(_players(), player_id, at)
