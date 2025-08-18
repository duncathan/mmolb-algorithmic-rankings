from collections.abc import Mapping
from typing import Final, Literal, NotRequired, TypedDict

type Category = Literal["Batting", "Pitching", "Baserunning", "Defense"]

type BattingAttribute = Literal[
    "Aiming",
    "Contact",
    "Cunning",
    "Discipline",
    "Insight",
    "Intimidation",
    "Lift",
    "Vision",
    "Determination",
    "Wisdom",
    "Muscle",
    "Selflessness",
]

type PitchingAttribute = Literal[
    "Accuracy",
    "Rotation",
    "Presence",
    "Persuasion",
    "Velocity",
    "Control",
    "Stuff",
    "Defiance",
    "Guts",
    "Stamina",
]

type BaserunningAttribute = Literal[
    "Greed",
    "Performance",
    "Speed",
    "Stealth",
]

type DefenseAttribute = Literal[
    "Acrobatics",
    "Agility",
    "Arm",
    "Awareness",
    "Composure",
    "Dexterity",
    "Patience",
    "Reaction",
    "Luck",
]

type Attribute = BattingAttribute | PitchingAttribute | BaserunningAttribute | DefenseAttribute

type Stars = str

BATTING_ATTRIBUTES: Final[tuple[BattingAttribute, ...]] = BattingAttribute.__value__.__args__
PITCHING_ATTRIBUTES: Final[tuple[PitchingAttribute, ...]] = PitchingAttribute.__value__.__args__
BASERUNNING_ATTRIBUTES: Final[tuple[BaserunningAttribute, ...]] = BaserunningAttribute.__value__.__args__
DEFENSE_ATTRIBUTES: Final[tuple[DefenseAttribute, ...]] = DefenseAttribute.__value__.__args__
ALL_ATTRIBUTES: Final[tuple[Attribute, ...]] = (
    BATTING_ATTRIBUTES + PITCHING_ATTRIBUTES + BASERUNNING_ATTRIBUTES + DEFENSE_ATTRIBUTES
)


class CategoryTalk[T: str = Attribute](TypedDict):
    quote: str
    season: NotRequired[int]
    day: NotRequired[int | str]
    stars: Mapping[T, Stars]


class ClubhouseTalk(TypedDict, total=False):
    Batting: CategoryTalk[BattingAttribute]
    Pitching: CategoryTalk[PitchingAttribute]
    Baserunning: CategoryTalk[BaserunningAttribute]
    Defense: CategoryTalk[DefenseAttribute]
