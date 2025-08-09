from typing import Literal, NotRequired, TypedDict


type Category = Literal['Batting', 'Pitching', 'Baserunning', 'Defense']

type BattingAttribute = Literal[
    'Aiming',
    'Contact',
    'Cunning',
    'Discipline',
    'Insight',
    'Intimidation',
    'Lift',
    'Vision',
    'Determination',
    'Wisdom',
    'Muscle',
    'Selflessness',
]

type PitchingAttribute = Literal[
    'Accuracy',
    'Rotation',
    'Presence',
    'Persuasion',
    'Velocity',
    'Control',
    'Stuff',
    'Defiance',
    'Guts',
    'Stamina',
]

type BaserunningAttribute = Literal[
    'Greed',
    'Performance',
    'Speed',
    'Stealth',
]

type DefenseAttribute = Literal[
    'Acrobatics',
    'Agility',
    'Arm',
    'Awareness',
    'Composure',
    'Dexterity',
    'Patience',
    'Reaction',
    'Luck',
]

type Attribute = BattingAttribute | PitchingAttribute | BaserunningAttribute | DefenseAttribute

type Stars = str

class CategoryTalk[T = Attribute](TypedDict):
    quote: str
    season: NotRequired[int]
    day: NotRequired[int | str]
    stars: dict[T, Stars]

class ClubhouseTalk(TypedDict, total=False):
    Batting: CategoryTalk[BattingAttribute]
    Pitching: CategoryTalk[PitchingAttribute]
    Baserunning: CategoryTalk[BaserunningAttribute]
    Defense: CategoryTalk[DefenseAttribute]

