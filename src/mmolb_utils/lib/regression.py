from collections import defaultdict

import pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import PolynomialFeatures

from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews.stats_api import StatFilter
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib import cached_ews
from mmolb_utils.lib.attributes import (
    BaserunningAttribute,
    BattingAttribute,
    PitchingAttribute,
)
from mmolb_utils.lib.stats import batting, pitching
from mmolb_utils.lib.stats.operations import StatOperation, StatTarget
from mmolb_utils.lib.time import SeasonDay

type Attributes[T: str] = dict[EntityID, dict[T, float]]


def get_attributes(
    kind: cashews.AnyCategoryTalk,
) -> Attributes:
    return {
        talk["entity_id"]: {attribute: len(stars) * 0.25 for attribute, stars in talk["data"]["stars"].items()}
        for talk in cached_ews.all_entities(kind)
    }


def run_regression(
    input_attributes: dict[EntityID, dict[str, float]],
    stat: StatOperation,
    stat_name: str,
    attr_names: list[str],
    *,
    degree: int = 1,
    start: SeasonDay | None = None,
    end: SeasonDay | None = None,
    season: int | None = None,
    filters: StatFilter = (),
) -> None:
    stat_dict = stat.evaluate_all(StatTarget.Player, start=start, end=end, season=season, filters=filters)

    data: dict[str, list[float]] = defaultdict(list)

    for player in sorted(input_attributes.keys() & stat_dict.keys()):
        for attribute, number in input_attributes[player].items():
            data[attribute].append(number)
        data[stat_name].append(stat_dict[player])

    df = pd.DataFrame(data)

    X = df[attr_names]
    y = df[stat_name]

    X = sm.add_constant(X)

    if degree > 1:
        poly = PolynomialFeatures(degree=2)
        X = poly.fit_transform(X)
        X = pd.DataFrame(X, columns=poly.get_feature_names_out())

    model = sm.OLS(y, X)
    result = model.fit()

    print(result.summary())


def batting_regression(
    stat: StatOperation,
    stat_name: str,
    *,
    degree: int = 1,
    start: SeasonDay | None = None,
    end: SeasonDay | None = None,
    season: int | None = None,
) -> None:
    batter_attr_names = [
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
    ]

    batting_attributes: Attributes[BattingAttribute] = get_attributes(cashews.EntityKind.TalkBatting)
    baserunning_attributes: Attributes[BaserunningAttribute] = get_attributes(cashews.EntityKind.TalkBaserunning)

    input_attributes: dict[EntityID, dict[str, float]] = {}

    for player, bat_attributes in batting_attributes.items():
        attributes: dict[str, float] = {attr: val for attr, val in bat_attributes.items()}
        if player in baserunning_attributes:
            attributes.update({attr: val for attr, val in baserunning_attributes[player].items()})
            input_attributes[player] = attributes

    run_regression(
        input_attributes,
        stat,
        stat_name,
        batter_attr_names,
        degree=degree,
        start=start,
        end=end,
        season=season,
        filters=(batting.PA > 120, batting.AB > 0),
    )


def pitching_regression(
    stat: StatOperation,
    stat_name: str,
    *,
    degree: int = 1,
    start: SeasonDay | None = None,
    end: SeasonDay | None = None,
    season: int | None = None,
) -> None:
    pitcher_attr_names = [
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

    pitching_attributes: Attributes[PitchingAttribute] = get_attributes(cashews.EntityKind.TalkPitching)

    run_regression(
        pitching_attributes,
        stat,
        stat_name,
        pitcher_attr_names,
        degree=degree,
        start=start,
        end=end,
        season=season,
        filters=pitching.IP > 25,
    )


if __name__ == "__main__":
    batting_regression(batting.OPS, "OPS", season=5)
    pitching_regression(pitching.ERA, "ERA", season=5)
