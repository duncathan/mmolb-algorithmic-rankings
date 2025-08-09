from collections import defaultdict
from typing import Literal, Self, TypedDict

import pandas as pd
import statsmodels.api as sm
from mmolb_utils.apis import cashews
from mmolb_utils.apis.cashews.types import SeasonDay, StatKey
from mmolb_utils.apis.mmolb import EntityID
from mmolb_utils.lib.attributes import BaserunningAttribute, BattingAttribute, ClubhouseTalk, DefenseAttribute, PitchingAttribute, Stars


class PlayerAttributes(TypedDict, total=False):
    Batting: dict[BattingAttribute, float]
    Pitching: dict[PitchingAttribute, float]
    Baserunning: dict[BaserunningAttribute, float]
    Defense: dict[DefenseAttribute, float]

    @classmethod
    def from_clubhouse(cls, clubhouse: ClubhouseTalk) -> Self:
        return cls({category: {attribute: len(stars) * 0.25 for attribute, stars in talk.items()} for category, talk in clubhouse.items()})

attr_names = [
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
    'Greed',
    'Performance',
    'Speed',
    'Stealth',
    'Luck',
]

batting_attributes: dict[EntityID, dict[BattingAttribute, Stars]] = {talk['entity_id']: talk['data']['stars'] for talk in cashews.get_entities(cashews.EntityKind.TalkBatting)}
baserunning_attributes: dict[EntityID, dict[BaserunningAttribute, Stars]] = {talk['entity_id']: talk['data']['stars'] for talk in cashews.get_entities(cashews.EntityKind.TalkBaserunning)}
pitching_attributes: dict[EntityID, dict[PitchingAttribute, Stars]] = {talk['entity_id']: talk['data']['stars'] for talk in cashews.get_entities(cashews.EntityKind.TalkPitching)}
defense_attributes: dict[EntityID, dict[DefenseAttribute, Stars]] = {talk['entity_id']: talk['data']['stars'] for talk in cashews.get_entities(cashews.EntityKind.TalkDefense)}

era_stats = cashews.get_stats(StatKey.EarnedRuns, StatKey.Outs, season=4, names=True)
era_dict = {stat['player_id']: (9 * stat['earned_runs'] / (stat['outs'] / 3)) for stat in era_stats if stat['outs']}

ops_stats = cashews.get_stats(StatKey.Singles, StatKey.Doubles, StatKey.Triples, StatKey.HomeRuns, StatKey.Walks, StatKey.HitByPitch, StatKey.PlateAppearances, StatKey.AtBats, season=4)
def ops(stat):
    hits = stat['singles'] + stat['doubles'] + stat['triples'] + stat['home_runs']
    obp = (hits + stat['walks'] + stat['hit_by_pitch']) / float(stat['plate_appearances'])
    slg = (stat['singles'] + stat['doubles'] * 2 + stat['triples'] * 3 + stat['home_runs'] * 4) / float(stat['at_bats'])
    return obp + slg
ops_dict = {stat['player_id']: ops(stat) for stat in ops_stats if stat['plate_appearances'] and stat['at_bats']}

input_attributes: dict[EntityID, dict[BattingAttribute | BaserunningAttribute | Literal['Luck'], float]] = {}
numerical_attributes = {entity: {attribute: len(stars) * 0.25 for attribute, stars in talk.items()} for entity, talk in batting_attributes.items()}

for player, attributes in numerical_attributes.items():
    if (player in baserunning_attributes) and (player in defense_attributes) and ("Luck" in defense_attributes[player]):
        attributes['Luck'] = len(defense_attributes[player]['Luck']) * 0.25
        attributes.update({attr: len(stars) * 0.25 for attr, stars in baserunning_attributes[player].items()})
        input_attributes[player] = attributes

data = defaultdict(list)

for player in sorted(input_attributes.keys() & ops_dict.keys()):
    for attribute, number in input_attributes[player].items():
        data[attribute].append(number)
    data['OPS'].append(ops_dict[player])

df = pd.DataFrame(data)

X = df[attr_names]
y = df['OPS']

X = sm.add_constant(X)
model = sm.OLS(y, X)
result = model.fit()

print(result.summary())