from collections.abc import Mapping, Sequence

_JsonPrimitive = str | int | float | bool | None

JsonObject_RO = Mapping[str, "JsonType_RO"]
JsonType_RO = JsonObject_RO | Sequence["JsonType_RO"] | _JsonPrimitive
"""Covariant type alias useful when accepting read-only input."""

JsonObject = dict[str, "JsonType"]
JsonType = JsonObject | list["JsonType"] | _JsonPrimitive
"""Invariant and mutable type alias. Use `typing.cast()` or a type guard if more specificity is needed."""
