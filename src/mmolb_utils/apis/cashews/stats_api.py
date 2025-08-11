from collections.abc import Iterable
from enum import Enum, auto
from typing import cast

from mmolb_utils.apis.cashews.misc import SeasonDay, SnakeCaseParam
from mmolb_utils.apis.cashews.request import _get_simple_data
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.json_lib import JsonObject


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
    filter_by: str | None = None,
    names: bool = False,
) -> list[JsonObject]:
    return cast(
        "list[JsonObject]",
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
            # filters
        ),
    )
