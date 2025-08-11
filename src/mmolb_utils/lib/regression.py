from collections import defaultdict
from typing import cast

import pandas as pd
import statsmodels.api as sm

from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews import StatKey
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.attributes import (
    BaserunningAttribute,
    BattingAttribute,
    DefenseAttribute,
    PitchingAttribute,
)

attr_names = [
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
    "Greed",
    "Performance",
    "Speed",
    "Stealth",
    "Luck",
]

type Attributes[T: str] = dict[EntityID, dict[T, float]]


def get_attributes(
    kind: cashews.EntityKind,
) -> Attributes:
    return {
        talk["entity_id"]: {
            attribute: len(stars) * 0.25  # type: ignore[arg-type]
            for attribute, stars in talk["data"]["stars"].items()  # type: ignore[call-overload, index, union-attr]
        }
        for talk in cashews.get_entities(kind)
    }


batting_attributes: Attributes[BattingAttribute] = get_attributes(cashews.EntityKind.TalkBatting)
baserunning_attributes: Attributes[BaserunningAttribute] = get_attributes(cashews.EntityKind.TalkBaserunning)
pitching_attributes: Attributes[PitchingAttribute] = get_attributes(cashews.EntityKind.TalkPitching)
defense_attributes: Attributes[DefenseAttribute] = get_attributes(cashews.EntityKind.TalkDefense)

era_stats = cashews.get_stats(StatKey.EarnedRuns, StatKey.Outs, season=4, names=True)
era_dict = {
    stat["player_id"]: (9 * stat["earned_runs"] / (stat["outs"] / 3))  # type: ignore[operator]
    for stat in era_stats
    if stat["outs"]
}

ops_stats = cashews.get_stats(
    StatKey.Singles,
    StatKey.Doubles,
    StatKey.Triples,
    StatKey.HomeRuns,
    StatKey.Walks,
    StatKey.HitByPitch,
    StatKey.PlateAppearances,
    StatKey.AtBats,
    season=4,
)


def ops(stat: dict[str, int]) -> float:
    hits = stat["singles"] + stat["doubles"] + stat["triples"] + stat["home_runs"]
    obp = (hits + stat["walks"] + stat["hit_by_pitch"]) / float(stat["plate_appearances"])
    slg = (stat["singles"] + stat["doubles"] * 2 + stat["triples"] * 3 + stat["home_runs"] * 4) / float(stat["at_bats"])
    return obp + slg


ops_dict = {
    stat["player_id"]: ops(cast("dict[str, int]", stat))
    for stat in ops_stats
    if stat["plate_appearances"] and stat["at_bats"]
}

input_attributes: dict[EntityID, dict[str, float]] = {}

for player, bat_attributes in batting_attributes.items():
    attributes: dict[str, float] = {attr: val for attr, val in bat_attributes.items()}
    if (player in baserunning_attributes) and (player in defense_attributes) and ("Luck" in defense_attributes[player]):
        attributes["Luck"] = defense_attributes[player]["Luck"]
        attributes.update({attr: val for attr, val in baserunning_attributes[player].items()})
        input_attributes[player] = attributes

data = defaultdict(list)

for player in sorted(input_attributes.keys() & ops_dict.keys()):
    for attribute, number in input_attributes[player].items():
        data[attribute].append(number)
    data["OPS"].append(ops_dict[player])

df = pd.DataFrame(data)

X = df[attr_names]
y = df["OPS"]

X = sm.add_constant(X)
model = sm.OLS(y, X)
result = model.fit()

print(result.summary())
