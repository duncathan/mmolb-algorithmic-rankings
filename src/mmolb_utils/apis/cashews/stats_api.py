from __future__ import annotations

import dataclasses
from collections.abc import Iterable
from enum import Enum, auto
from typing import Literal, Required, TypedDict, TypeGuard, cast

from mmolb_utils.apis.cashews.misc import SnakeCaseParam
from mmolb_utils.apis.cashews.request import _get_simple_data
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.time import SeasonDay


class StatKey(SnakeCaseParam, Enum):
    AllowedStolenBases = 0
    Appearances = 1
    Assists = 2
    AtBats = 3
    BattersFaced = 4
    BlownSaves = 5
    CaughtDoublePlay = 6
    CaughtStealing = 7
    CompleteGames = 8
    DoublePlays = 9
    Doubles = 10
    EarnedRuns = 11
    Errors = 12
    FieldOut = 13
    FieldersChoice = 14
    Flyouts = 15
    ForceOuts = 16
    GamesFinished = 17
    GroundedIntoDoublePlay = 18
    Groundouts = 19
    HitBatters = 20
    HitByPitch = 21
    HitsAllowed = 22
    HomeRuns = 23
    HomeRunsAllowed = 24
    InheritedRunners = 25
    InheritedRunsAllowed = 26
    LeftOnBase = 27
    Lineouts = 28
    Losses = 29
    MoundVisits = 30
    NoHitters = 31
    Outs = 32
    PerfectGames = 33
    PitchesThrown = 34
    PlateAppearances = 35
    Popouts = 36
    Putouts = 37
    QualityStarts = 38
    ReachedOnError = 39
    RunnersCaughtStealing = 40
    Runs = 41
    RunsBattedIn = 42
    SacFlies = 43
    SacrificeDoublePlays = 44
    Saves = 45
    Shutouts = 46
    Singles = 47
    Starts = 48
    StolenBases = 49
    Strikeouts = 50
    StruckOut = 51
    Triples = 52
    UnearnedRuns = 53
    Walked = 54
    Walks = 55
    Wins = 56

    def _filter(self, other: object, op: FilterOp) -> _StatFilter:
        if not isinstance(other, int):
            raise NotImplementedError
        return _StatFilter(self, op, other)

    def __gt__(self, other: object) -> _StatFilter:
        return self._filter(other, "gt")

    def __lt__(self, other: object) -> _StatFilter:
        return self._filter(other, "lt")

    def __eq__(self, other: object) -> _StatFilter:  # type: ignore[override]
        return self._filter(other, "eq")

    def __le__(self, other: object) -> _StatFilter:
        return self._filter(other, "lte")

    def __ge__(self, other: object) -> _StatFilter:
        return self._filter(other, "gte")


class GroupColumn(SnakeCaseParam, Enum):
    Player = auto()
    Team = auto()
    League = auto()
    Season = auto()
    Day = auto()
    """implies season"""
    Game = auto()
    # Slot = auto()
    PlayerName = auto()


FilterOp = Literal["gt", "lt", "eq", "lte", "gte"]


def is_filter_iterable(value: object) -> TypeGuard[Iterable[_StatFilter]]:
    if not isinstance(value, Iterable):
        return False
    return all(isinstance(subvalue, _StatFilter) for subvalue in value)


@dataclasses.dataclass(frozen=True)
class _StatFilter:
    stat: StatKey
    op: FilterOp
    value: int

    @property
    def param_name(self) -> str:
        return f"filter[{self.stat.url_param}][{self.op}]"

    def __and__(self, other: object) -> tuple[_StatFilter, ...]:
        if isinstance(other, _StatFilter):
            return (self, other)
        if is_filter_iterable(other):
            return (self, *other)
        raise NotImplementedError


type StatFilter = _StatFilter | Iterable[_StatFilter]


class StatRow(TypedDict, total=False):
    player_id: Required[str]
    player_name: str
    allowed_stolen_bases: int
    appearances: int
    assists: int
    at_bats: int
    batters_faced: int
    blown_saves: int
    caught_double_play: int
    caught_stealing: int
    complete_games: int
    double_plays: int
    doubles: int
    earned_runs: int
    errors: int
    field_out: int
    fielders_choice: int
    flyouts: int
    force_outs: int
    games_finished: int
    grounded_into_double_play: int
    groundouts: int
    hit_batters: int
    hit_by_pitch: int
    hits_allowed: int
    home_runs: int
    home_runs_allowed: int
    inherited_runners: int
    inherited_runs_allowed: int
    left_on_base: int
    lineouts: int
    losses: int
    mound_visits: int
    no_hitters: int
    outs: int
    perfect_games: int
    pitches_thrown: int
    plate_appearances: int
    popouts: int
    putouts: int
    quality_starts: int
    reached_on_error: int
    runners_caught_stealing: int
    runs: int
    runs_batted_in: int
    sac_flies: int
    sacrifice_double_plays: int
    saves: int
    shutouts: int
    singles: int
    starts: int
    stolen_bases: int
    intikeouts: int
    intuck_out: int
    triples: int
    unearned_runs: int
    walked: int
    walks: int
    wins: int


def get_stats(  # noqa: C901
    *fields: StatKey,
    group: GroupColumn | Iterable[GroupColumn] = GroupColumn.Player,
    start: SeasonDay | None = None,
    end: SeasonDay | None = None,
    season: int | None = None,
    player: EntityID | None = None,
    team: EntityID | None = None,
    league: EntityID | None = None,
    game: EntityID | None = None,
    sort: StatKey | None = None,
    count: int | None = None,
    filters: StatFilter = (),
    names: bool = False,
) -> list[StatRow]:
    if isinstance(filters, _StatFilter):
        filters = (filters,)

    filter_dict = {filt.param_name: filt.value for filt in filters}

    return cast(
        "list[StatRow]",
        _get_simple_data(
            "stats",
            format="json",
            fields=fields,
            group=group,
            start=start,
            end=end,
            season=season,
            player=player,
            team=team,
            league=league,
            game=game,
            sort=sort,
            count=count,
            names=names,
            **filter_dict,
        ),
    )
