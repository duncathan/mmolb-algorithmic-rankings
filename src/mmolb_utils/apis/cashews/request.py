import typing
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime
from http.client import responses

import requests

from mmolb_utils.lib.json_lib import JsonObject, JsonType

CASHEWS_API = "https://freecashe.ws/api"

_RawParam = str | int | float | None


class Paramable(typing.Protocol):
    @property
    def url_param(self) -> _RawParam: ...


type Param = _RawParam | bool | datetime | Paramable | Iterable["Param"]


def _encode_param(param: Param) -> _RawParam:
    if isinstance(param, bool):
        return str(param).lower()

    if isinstance(param, datetime):
        return param.isoformat()

    if isinstance(param, _RawParam):
        return param

    if isinstance(param, Iterable):
        return ",".join(str(_encode_param(sub_param)) for sub_param in param)

    return param.url_param


def _get_simple_data(endpoint: str, **params: Param) -> JsonType:
    url = f"{CASHEWS_API}/{endpoint}"

    encoded_params = {param: _encode_param(value) for param, value in params.items()}
    response = requests.get(url, encoded_params)
    # print(response.url)

    if (code := response.status_code) in {400, 500}:
        raise requests.HTTPError(f"{code} {responses[code]}: '{response.text}'", response=response)

    response.raise_for_status()  # handle other errors

    return response.json()


type PageToken = str


class PaginatedResult[T = JsonType](typing.TypedDict):
    items: list[T]
    next_page: PageToken | None


_print_progress = True


def set_print_progress(value: bool) -> None:
    global _print_progress
    _print_progress = value


@contextmanager
def suppress_prints():
    old_value = _print_progress
    set_print_progress(False)
    try:
        yield None
    finally:
        set_print_progress(old_value)


def _get_paginated_data[T = JsonObject](
    endpoint: str,
    name: str | None,
    _kind: type[T],
    **params: Param,
) -> Iterator[T]:
    global _print_progress

    page_num = 0
    next_page = None
    got_first_page = False

    while (not got_first_page) or next_page is not None:
        got_first_page = True
        page_num += 1

        data = typing.cast("PaginatedResult[T] | list[T]", _get_simple_data(endpoint, **params, page=next_page))

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
