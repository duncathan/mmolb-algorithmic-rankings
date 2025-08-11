from collections import defaultdict
from collections.abc import Callable
from typing import cast

import pandas as pd
import statsmodels.api as sm

from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews import StatKey
from mmolb_utils.apis.cashews.stats_api import StatRow
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.attributes import (
    BaserunningAttribute,
    BattingAttribute,
    PitchingAttribute,
)

# attr_names = [
#     "Aiming",
#     "Contact",
#     "Cunning",
#     "Discipline",
#     "Insight",
#     "Intimidation",
#     "Lift",
#     "Vision",
#     "Determination",
#     "Wisdom",
#     "Muscle",
#     "Selflessness",
#     "Greed",
#     "Performance",
#     "Speed",
#     "Stealth",
# ]

attr_names = [
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

type Attributes[T: str] = dict[EntityID, dict[T, float]]


def get_attributes(
    kind: cashews.AnyCategoryTalk,
) -> Attributes:
    return {
        talk["entity_id"]: {attribute: len(stars) * 0.25 for attribute, stars in talk["data"]["stars"].items()}
        for talk in cashews.get_entities(kind)
    }


batting_attributes: Attributes[BattingAttribute] = get_attributes(cashews.EntityKind.TalkBatting)
baserunning_attributes: Attributes[BaserunningAttribute] = get_attributes(cashews.EntityKind.TalkBaserunning)
pitching_attributes: Attributes[PitchingAttribute] = get_attributes(cashews.EntityKind.TalkPitching)
# defense_attributes: Attributes[DefenseAttribute] = get_attributes(cashews.EntityKind.TalkDefense)

batting_stats = cashews.get_stats(
    StatKey.Singles,
    StatKey.Doubles,
    StatKey.Triples,
    StatKey.HomeRuns,
    StatKey.Walked,
    StatKey.HitByPitch,
    StatKey.PlateAppearances,
    StatKey.AtBats,
    StatKey.SacFlies,
    StatKey.StruckOut,
    season=4,
    filters=(StatKey.PlateAppearances > 100) & (StatKey.AtBats > 0),
)


def obp(stat: dict[str, int]) -> float:
    hits = stat["singles"] + stat["doubles"] + stat["triples"] + stat["home_runs"]
    return (hits + stat["walked"] + stat["hit_by_pitch"]) / float(stat["plate_appearances"])


def slg(stat: dict[str, int]) -> float:
    return (stat["singles"] + stat["doubles"] * 2 + stat["triples"] * 3 + stat["home_runs"] * 4) / float(
        stat["at_bats"]
    )


def walk_rate(stat: dict[str, int]) -> float:
    return stat["walked"] / stat["plate_appearances"]


def babip(stat: dict[str, int]) -> float:
    hits = stat["singles"] + stat["doubles"] + stat["triples"] + stat["home_runs"]
    balls_in_play = stat["at_bats"] - stat["struck_out"] - stat["home_runs"] + stat["sac_flies"]
    return (hits - stat["home_runs"]) / balls_in_play


def stat_dict(stats: list[StatRow], formula: Callable[[dict[str, int]], float]) -> dict[EntityID, float]:
    return {
        stat["player_id"]: formula(cast("dict[str, int]", stat))
        for stat in stats
        if (stat.get("at_bats") and stat.get("plate_appearances", 0) > 100)
        or (stat.get("outs", 0) > 120 and stat.get("starts"))
        # or stat.get("wins") or stat.get("losses")
    }


obp_dict = stat_dict(batting_stats, obp)
slg_dict = stat_dict(batting_stats, slg)
ops_dict = stat_dict(batting_stats, lambda stat: obp(stat) + slg(stat))
walk_rate_dict = stat_dict(batting_stats, walk_rate)
babip_dict = stat_dict(batting_stats, babip)

era_stats = cashews.get_stats(
    StatKey.EarnedRuns,
    StatKey.Outs,
    StatKey.Wins,
    StatKey.Losses,
    StatKey.Appearances,
    StatKey.BattersFaced,
    StatKey.PitchesThrown,
    StatKey.Starts,
    season=4,
    filters=(StatKey.Outs > 120) & (StatKey.AllowedStolenBases == 0),
)


def era(stat: dict[str, int]) -> float:
    return 9 * stat["earned_runs"] / (stat["outs"] / 3)


# era_dict = stat_dict(era_stats, era)
# top_quartile = np.percentile(list(era_dict.values()), 25)
# era_dict = {player: era for player, era in era_dict.items() if era < top_quartile}
win_dict = stat_dict(era_stats, lambda stat: stat["pitches_thrown"] / stat["batters_faced"])
# starters: set[EntityID] = set()
# for player in cashews.get_entities(cashews.EntityKind.PlayerLite):
#     if player['data']['Position'] in {"SP1", "SP2", "SP3", "SP4", "SP5", "SP"}:
#         starters.add(player['entity_id'])
# win_dict = {player: win for player, win in win_dict.items() if player in starters}

input_attributes: dict[EntityID, dict[str, float]] = {}

for player, bat_attributes in batting_attributes.items():
    attributes: dict[str, float] = {attr: val for attr, val in bat_attributes.items()}
    if player in baserunning_attributes:
        attributes.update({attr: val for attr, val in baserunning_attributes[player].items()})
        input_attributes[player] = attributes

data: dict[str, list[float]] = defaultdict(list)

for player in sorted(pitching_attributes.keys() & win_dict.keys()):
    for attribute, number in pitching_attributes[player].items():
        data[attribute].append(number)
    data["PT/BF"].append(win_dict[player])

df = pd.DataFrame(data)

X = df[attr_names]
y = df["PT/BF"]

X = sm.add_constant(X)

# poly = PolynomialFeatures(degree=2)
# X = poly.fit_transform(X)
# X = pd.DataFrame(X, columns=poly.get_feature_names_out())

model = sm.OLS(y, X)
result = model.fit()

print(result.summary())
