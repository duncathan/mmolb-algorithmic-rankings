from enum import IntEnum, auto
from typing import Literal, NamedTuple, TypeAlias, TypedDict

from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.json_lib import JsonObject, JsonType


type PageToken = str

class PaginatedResult[T: JsonType = JsonType](TypedDict):
    items: list[T]
    next_page: PageToken | None

type SortOrder = Literal["asc", "desc"]

class EntityKind(IntEnum):
    State = 1
    League = 2
    Team = 3
    Player = 4
    Game = 5

    Time = 6
    Nouns = 7
    Adjectives = 8

    PlayerLite = 9
    TeamLite = 10

    News = 11
    Spotlight = 12
    Election = 13

    GamesEndpoint = 14
    PostseasonBracket = 15
    Message = 16

    Schedule = 17
    """*Deprecated*"""

    Season = 18
    Day = 19
    PatchNotes = 20

    Talk = 21
    TalkBatting = 22
    TalkPitching = 23
    TalkBaserunning = 24
    TalkDefense = 25

    SuperstarGames = 26

    PlayerFeed = 27
    TeamFeed = 28


type IsoDateTime = str

class SeasonDay(NamedTuple):
    season: int
    day: int

    @property
    def url_param(self) -> str:
        return f"{self.season},{self.day}"

class EntityVersion[T: JsonType = JsonType](TypedDict):
    kind: str
    """Always a valid `EntityKind` value"""

    entity_id: EntityID
    valid_from: IsoDateTime
    valid_to: IsoDateTime | None
    data: T

CashewsGame: TypeAlias = JsonObject # TODO: TypedDict
CashewsTeam: TypeAlias = JsonObject # TODO: TypedDict
CashewsLeague: TypeAlias = JsonObject # TODO: TypedDict
CashewsPlayerStats: TypeAlias = JsonObject # TODO: TypedDict
CashewsScorigami: TypeAlias = JsonObject # TODO: TypedDict
CashewsLocation: TypeAlias = JsonObject # TODO: TypedDict


class StatKey(IntEnum):
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


class GroupColumn(IntEnum):
    Player = auto()
    Team = auto()
    League = auto()
    Season = auto()
    Day = auto()
    """implies season"""
    Game = auto()
    # Slot = auto()
    PlayerName = auto()
