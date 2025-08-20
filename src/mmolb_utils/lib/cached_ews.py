import functools
import json
from collections import defaultdict
from collections.abc import Container, Iterator
from datetime import UTC, datetime, timedelta

import jsonlines
import platformdirs
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper

from mmolb_utils.apis import cashews, mmolb
from mmolb_utils.apis.cashews.request import suppress_prints
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.io import safe_write

_perform_cacheing = True


def set_use_cache(value: bool) -> None:
    global _perform_cacheing
    _perform_cacheing = value


_ids = ()


def set_ids(value: tuple[EntityID, ...]) -> None:
    global _ids
    _ids = value


class IterCallbackIOWrapper(CallbackIOWrapper):
    def __init__(self, callback, stream, method="read") -> None:
        super().__init__(callback, stream, method)
        if method == "read":
            func = getattr(stream, "__iter__")

            @functools.wraps(func)
            def __iter__(*args, **kwargs):
                for data in func(*args, **kwargs):
                    callback(len(data))
                    yield data

            self.wrapper_setattr("iter", __iter__)

    def __iter__(self):
        yield from self.wrapper_getattr("iter")()


@functools.lru_cache
def _cached_entities(kind: cashews.EntityKind) -> dict[EntityID, list[dict]]:
    cache = platformdirs.user_cache_path("mmolb_utils")
    cache.mkdir(parents=True, exist_ok=True)
    local_file = cache.joinpath(f"{kind.url_param}.jsonl")
    metadata_file = cache.joinpath("metadata.json")

    timestamp = now()
    entities = defaultdict(list)

    # Load cache from storage

    load_pbar = tqdm(
        total=local_file.stat().st_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        leave=False,
        desc=f"Loading {kind.name}",
    )

    try:
        with metadata_file.open("r") as meta:
            metadata = json.load(meta)
    except (json.JSONDecodeError, FileNotFoundError):
        metadata = {}

    try:
        with local_file.open("r", encoding="utf_8") as file:
            wrapped = IterCallbackIOWrapper(load_pbar.update, file, "read")
            with jsonlines.Reader(wrapped) as reader:
                for obj in reader:
                    entities.update(obj)

    except (json.JSONDecodeError, FileNotFoundError):
        metadata[kind.url_param] = None

    after = metadata.get(kind.url_param)
    if after is not None:
        after = datetime.fromisoformat(after)

    if (after is not None) and timestamp - after < timedelta(hours=1):
        load_pbar.close()
        return entities

    # Update cache from chron

    if kind in {
        cashews.EntityKind.Day,
        cashews.EntityKind.Season,
        cashews.EntityKind.PlayerFeed,
        cashews.EntityKind.TeamFeed,
    }:
        entities = defaultdict(list)
        entity_iter = functools.partial(
            cashews.get_entities,
            kind,
            order="desc",
        )
    else:
        entity_iter = functools.partial(
            cashews.get_versions,
            kind,
            order="desc",
            after=after,
            before=now() - timedelta(hours=1),
        )

    with suppress_prints():
        update_pbar = tqdm(
            entity_iter(),
            leave=False,
            desc=f"Updating {kind.name}",
        )
        for entity in update_pbar:
            entities[entity["entity_id"]].append(entity)

    # Save cache to file

    save_pbar = tqdm(
        entities.items(),
        leave=False,
        desc=f"Saving {kind.name}",
    )

    with safe_write(local_file, encoding="utf_8") as file:
        with jsonlines.Writer(file) as writer:
            for entity_id, versions in save_pbar:
                writer.write({entity_id: versions})

        metadata[kind.url_param] = timestamp.isoformat()
        with safe_write(metadata_file) as meta:
            json.dump(metadata, meta)

    save_pbar.close()
    update_pbar.close()
    load_pbar.close()

    return entities


def all_entities(kind: cashews.EntityKind, id: Container[EntityID] | None = None) -> Iterator[dict]:
    for entity_id, versions in _cached_entities(kind).items():
        if (id is None) or (entity_id in id):
            yield from versions


def get_entity(kind: cashews.EntityKind, entity_id: EntityID, at: datetime | None = None) -> dict | None:
    if not _perform_cacheing:
        return next(cashews.get_entities(kind, id=entity_id, at=at), None)
    entities = _cached_entities(kind)
    versions = entities[entity_id]
    if not versions:
        if kind == cashews.EntityKind.PlayerFeed:
            return {"data": mmolb.get_player_feed(entity_id)}
        return None
    if at is None:
        at = now()
    return next(
        (version for version in versions if datetime.fromisoformat(version["valid_from"]) < at),
        versions[-1],
    )


def get_earliest(kind: cashews.EntityKind, entity_id: EntityID) -> dict | None:
    if not _perform_cacheing:
        return next(cashews.get_versions(kind, id=entity_id), None)
    entities = _cached_entities(kind)
    versions = entities[entity_id]
    if not versions:
        if kind == cashews.EntityKind.PlayerFeed:
            return {"data": mmolb.get_player_feed(entity_id)}
        return None
    return min(versions, key=lambda ver: datetime.fromisoformat(ver["valid_from"]))


@functools.lru_cache
def now() -> datetime:
    return datetime.now(UTC)
