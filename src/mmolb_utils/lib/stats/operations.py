from __future__ import annotations

import dataclasses
import functools
import itertools
from collections import defaultdict
from collections.abc import Iterable, Iterator
from enum import Enum, auto
from typing import ClassVar, Literal

from frozendict import frozendict

from mmolb_utils.apis.cashews.stats_api import (
    FilterableStat,
    FilterOp,
    GroupColumn,
    StatKey,
    StatRow,
    get_stats,
)
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.time import SeasonDay


@dataclasses.dataclass(frozen=True)
class StatOpFilter:
    lhs: StatOperation | float
    rhs: StatOperation | float
    op: FilterOp

    def applies(
        self,
        target: StatTarget,
        entity_id: EntityID,
        start: SeasonDay | None = None,
        end: SeasonDay | None = None,
        season: int | None = None,
    ) -> bool:
        if isinstance(self.lhs, StatOperation):
            lhs = self.lhs.evaluate_individual(target, entity_id, start, end, season, filters=())
        else:
            lhs = self.lhs

        if isinstance(self.rhs, StatOperation):
            rhs = self.rhs.evaluate_individual(target, entity_id, start, end, season, filters=())
        else:
            rhs = self.rhs

        match self.op:
            case "eq":
                return lhs == rhs
            case "gt":
                return lhs > rhs
            case "gte":
                return lhs >= rhs
            case "lt":
                return lhs < rhs
            case "lte":
                return lhs <= rhs


class StatTarget(Enum):
    Player = auto()
    Team = auto()
    League = auto()
    # PlayerAgainst = auto()
    TeamAgainst = auto()
    MatchmakingFactor = auto()


class StatOpMixin:
    """Helper class just to split out the operator overloading definitions"""

    def _operation(self, other: object, op: ArithmeticOp, is_rhs: bool = False) -> StatOperation:
        assert isinstance(self, StatOperation)
        if not isinstance(other, Operand):
            return NotImplemented

        if other == 1 and (op == "*" or (op == "/" and not is_rhs)):
            return self  # multiplicative identity

        if other == 0 and (op == "+" or (op == "-" and not is_rhs)):
            return self  # additive identity

        if not is_rhs:
            return StatOperation(self, other, op)
        else:
            return StatOperation(other, self, op)

    # associative
    def __add__(self, other: object) -> StatOperation:
        return self._operation(other, "+")

    __radd__ = __add__

    def __mul__(self, other: object) -> StatOperation:
        return self._operation(other, "*")

    __rmul__ = __mul__

    # non-associative
    def __sub__(self, other: object) -> StatOperation:
        return self._operation(other, "-")

    def __rsub__(self, other: object) -> StatOperation:
        return self._operation(other, "-", True)

    def __truediv__(self, other: object) -> StatOperation:
        return self._operation(other, "/")

    def __rtruediv__(self, other: object) -> StatOperation:
        return self._operation(other, "/", True)

    def __floordiv__(self, other: object) -> StatOperation:
        return self._operation(other, "//")

    def __rfloordiv__(self, other: object) -> StatOperation:
        return self._operation(other, "//", True)

    def __divmod__(self, other: object) -> StatOperation:
        return self._operation(other, "%")

    def __rdivmod__(self, other: object) -> StatOperation:
        return self._operation(other, "%", True)

    def __neg__(self) -> StatOperation:
        if self.lhs == 0 and self.op == "-" and isinstance(self.rhs, StatOperation):
            # undo the previous negation step to minimize redundant nesting
            return self.rhs
        return 0 - self


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class StatOperation(StatOpMixin, FilterableStat[StatOpFilter]):
    lhs: Operand
    rhs: Operand
    op: ArithmeticOp

    _evaluation_cache: dict[EntityID, float] = dataclasses.field(
        default_factory=dict, init=False, hash=False, repr=False, compare=False
    )

    type _CacheTuple = tuple[StatTarget, SeasonDay | None, SeasonDay | None, int | None]
    _stat_cache: ClassVar[dict[_CacheTuple, dict[EntityID, dict[StatKey, float]]]] | None = None

    def _filter(self, other: object, op: FilterOp) -> StatOpFilter:
        if not isinstance(other, StatOperation | float):
            return NotImplemented

        return StatOpFilter(self, other, op)

    def __str__(self) -> str:
        return f"({str(self.lhs)} {self.op} {str(self.rhs)})"

    def all_stat_keys(self) -> Iterator[StatKey]:
        for operand in (self.lhs, self.rhs):
            if isinstance(operand, StatOperation):
                yield from operand.all_stat_keys()
            elif isinstance(operand, StatKey):
                yield operand

    @staticmethod
    def _simple_stat_calc(
        to_pull: list[StatKey],
        cache: dict[EntityID, dict[StatKey, float]],
        start: SeasonDay | None,
        end: SeasonDay | None,
        season: int | None,
        group: GroupColumn,
        id_key: str,
    ) -> None:
        stats = get_stats(*to_pull, group=group, start=start, end=end, season=season)
        for row in stats:
            for stat in to_pull:
                cache[row[id_key]][stat] = row[stat.url_param]

    @staticmethod
    def _team_against_calc(
        to_pull: list[StatKey],
        cache: dict[EntityID, dict[StatKey, float]],
        start: SeasonDay | None,
        end: SeasonDay | None,
        season: int | None,
    ) -> None:
        if season is not None:
            start = SeasonDay(season, 0)
            end = SeasonDay(season, 300)

        assert end is not None
        start = start or SeasonDay(0, 0)

        stats = []
        for season in range(start.season, end.season + 1):
            # really ugly pagination stuff because oops too many rows!
            start_day, end_day = 0, 300

            if season == start.season:
                start_day = start.day
            if season == end.season:
                end_day = end.day

            for dates in itertools.batched(range(start_day, end_day + 1), 40):
                stats.extend(
                    get_stats(
                        *to_pull,
                        group=(GroupColumn.Team, GroupColumn.Game),
                        start=SeasonDay(season, dates[0]),
                        end=SeasonDay(season, dates[-1]),
                    )
                )

        team_to_game_stats: dict[EntityID, list[StatRow]] = defaultdict(list)
        game_id_to_game_stats: dict[EntityID, list[StatRow]] = defaultdict(list)

        for row in stats:
            team_to_game_stats[row["team_id"]].append(row)
            game_id_to_game_stats[row["game_id"]].append(row)

        for stat in to_pull:
            for team, games in team_to_game_stats.items():
                total = 0
                for game in games:
                    game_row = next(row for row in game_id_to_game_stats[game["game_id"]] if row != game)
                    total += game_row[stat.url_param]
                cache[team][stat] = total

    @classmethod
    @functools.cache
    def _stats(
        cls,
        *fields: StatKey,
        target: StatTarget,
        start: SeasonDay | None = None,
        end: SeasonDay | None = None,
        season: int | None = None,
        filters: Iterable[StatOpFilter] = (),
    ) -> frozendict[EntityID, frozendict[StatKey, float]]:
        if cls._stat_cache is None:
            cls._stat_cache = {}

        cache_key = (target, start, end, season)
        cls._stat_cache.setdefault(cache_key, defaultdict(dict))
        cache = cls._stat_cache[cache_key]

        if cache:
            to_pull = [stat for stat in fields if stat not in next(iter(cache.values()))]
        else:
            to_pull = list(fields)

        simple_calc = functools.partial(cls._simple_stat_calc, to_pull, cache, start, end, season)

        if to_pull:
            match target:
                case StatTarget.Player:
                    simple_calc(GroupColumn.Player, "player_id")
                case StatTarget.Team:
                    simple_calc(GroupColumn.Team, "team_id")
                case StatTarget.League:
                    simple_calc(GroupColumn.League, "league_id")
                case StatTarget.TeamAgainst:
                    cls._team_against_calc(to_pull, cache, start, end, season)
                case _:
                    raise NotImplementedError

        return frozendict(
            {
                entity: frozendict(entity_stats)
                for entity, entity_stats in cache.items()
                if all(filt.applies(target, entity, start, end, season) for filt in filters)
            }
        )

    def _perform_op(self, lhs: float, rhs: float) -> float:
        match self.op:
            case "+":
                return lhs + rhs
            case "-":
                return lhs - rhs
            case "*":
                return lhs * rhs
            case "/":
                return lhs / rhs
            case "//":
                return lhs // rhs
            case "%":
                return lhs % rhs

    @functools.lru_cache
    def _evaluate_single(
        self,
        stats: frozendict[StatKey, float],
    ):
        def eval_operand(operand: Operand) -> float:
            if isinstance(operand, StatOperation):
                return operand._evaluate_single(stats)
            elif isinstance(operand, StatKey):
                return stats[operand]
            else:
                return operand

        lhs = eval_operand(self.lhs)
        rhs = eval_operand(self.rhs)

        return self._perform_op(lhs, rhs)

    def evaluate_individual(
        self,
        target: StatTarget,
        entity_id: EntityID,
        start: SeasonDay | None = None,
        end: SeasonDay | None = None,
        season: int | None = None,
        filters: Iterable[StatOpFilter] = (),
    ) -> float:
        # if target is StatTarget.MatchmakingFactor:
        #     against = self._stats(
        #         *self.all_stat_keys(),
        #         target=StatTarget.TeamAgainst,
        #         start=start,
        #         end=end,
        #         season=season,
        #         filters=filters,
        #     )
        #     league = self._stats(
        #         *self.all_stat_keys(),
        #         target=target,
        #         start=start,
        #         end=end,
        #         season=season,
        #         filters=filters,
        #     )
        # else:
        all_stats = self._stats(
            *self.all_stat_keys(),
            target=target,
            start=start,
            end=end,
            season=season,
            filters=filters,
        )

        if entity_id not in all_stats:
            raise ValueError(
                f"Entity ID does not exist within the constraints of {start=}, {end=}, {season=}, {filters=}"
            )

        return self._evaluate_single(all_stats[entity_id])

    def evaluate_all(
        self,
        target: StatTarget,
        start: SeasonDay | None = None,
        end: SeasonDay | None = None,
        season: int | None = None,
        filters: Iterable[StatOpFilter] = (),
    ) -> frozendict[EntityID, float]:
        all_stats = self._stats(
            *self.all_stat_keys(),
            target=target,
            start=start,
            end=end,
            season=season,
            filters=filters,
        )

        return frozendict({entity_id: self._evaluate_single(stats) for entity_id, stats in all_stats.items()})


def RawStat(stat: StatKey) -> StatOperation:
    return StatOperation(stat, 0, "+")


Operand = StatOperation | StatKey | float | int
ArithmeticOp = Literal["+", "-", "*", "/", "//", "%"]
