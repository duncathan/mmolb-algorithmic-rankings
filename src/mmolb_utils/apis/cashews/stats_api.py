from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Iterator
from enum import Enum, auto
from typing import Literal, Self, TypedDict, cast

from mmolb_utils.apis.cashews.misc import SnakeCaseParam
from mmolb_utils.apis.cashews.request import _get_simple_data
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.time import SeasonDay

FilterOp = Literal["gt", "lt", "eq", "lte", "gte"]


class FilterableStat[T]:
    def __iter__(self) -> Iterator[Self]:
        # makes it convenient to just accept iterables of the type
        yield self

    def _filter(self, other: object, op: FilterOp) -> T:
        """Returns the filter object according to the value and operation"""
        raise NotImplementedError

    def __gt__(self, other: object) -> T:
        return self._filter(other, "gt")

    def __lt__(self, other: object) -> T:
        return self._filter(other, "lt")

    def __eq__(self, other: object) -> T:  # type: ignore[override]
        return self._filter(other, "eq")

    def __le__(self, other: object) -> T:
        return self._filter(other, "lte")

    def __ge__(self, other: object) -> T:
        return self._filter(other, "gte")


@dataclasses.dataclass(frozen=True)
class StatFilter:
    stat: StatKey
    op: FilterOp
    value: int

    @property
    def param_name(self) -> str:
        return f"filter[{self.stat.url_param}][{self.op}]"


class StatKey(SnakeCaseParam, FilterableStat[StatFilter], Enum):
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

    def __hash__(self) -> int:
        # required since we override __eq__ for filters
        return hash(self.name)

    def _filter(self, other: object, op: FilterOp) -> StatFilter:
        if not isinstance(other, int):
            return NotImplemented
        return StatFilter(self, op, other)


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


class StatRow(TypedDict, total=False):
    player_id: EntityID
    player_name: str
    team_id: EntityID
    league_id: EntityID
    season: int
    day: int
    game_id: EntityID
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


def get_stats(
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
    filters: Iterable[StatFilter] = (),
    names: bool = False,
) -> list[StatRow]:
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
