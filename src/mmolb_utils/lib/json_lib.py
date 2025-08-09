from collections.abc import Mapping, Sequence

type _JsonPrimitive = str | int | float | bool | None

type JsonObject_RO = Mapping[str, "JsonType_RO"]
type JsonType_RO = JsonObject_RO | Sequence["JsonType_RO"] | _JsonPrimitive
"""Covariant type alias useful when accepting read-only input."""

type JsonObject = dict[str, "JsonType"]
type JsonType = JsonObject | list["JsonType"] | _JsonPrimitive
"""Invariant and mutable type alias. Use `typing.cast()` or a type guard if more specificity is needed."""
