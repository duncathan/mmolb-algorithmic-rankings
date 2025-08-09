from collections import defaultdict
import json
from statistics import mean, stdev
from typing import Literal

from mmolb_utils.apis.cashews import api as cashews
from mmolb_utils.lib.duel import players_in_duel

highest_star = 0
highest_star_owners = []

attr_counts = {
    'Batting': 12,
    'Pitching': 10,
    'Baserunning': 4,
    'Defense': 8,
}

star_counts: dict[Literal['Batting', 'Baserunning', 'Defense', 'Pitching'], list[int]] = defaultdict(list)

SEASON_4 = "6887d44218e81770515b6218"

pitcher_ids = []
batter_ids = []

for player in cashews.get_entities(cashews.EntityKind.Player):
    if SEASON_4 not in player['data']['Stats']:
        continue
    print(player)
    raise ValueError

for talk in cashews.get_entities(cashews.EntityKind.Talk):
    if talk['entity_id'] in players_in_duel():
        continue
    
    for category, info in talk['data'].items():
        full_stars = "".join(info['stars'].values())
        star_counts[category].append(len(full_stars))
        highest = max(len(attr) for attr in info['stars'].values())
        old_highest_star = highest_star
        highest_star = max(highest, highest_star)
        if old_highest_star != highest_star:
            highest_star_owners = []
        if highest_star == highest:
            highest_star_owners.append(talk['entity_id'])

sample_size = {category: len(counts) for category, counts in star_counts.items()}

averages = {category: mean(counts) for category, counts in star_counts.items()}

std_devs = {category: stdev(counts) for category, counts in star_counts.items()}

normalized = {category: average / attr_counts[category] for category, average in averages.items()}

std_devs_norm = {category: std_dev / attr_counts[category] for category, std_dev in std_devs.items()}

results = {
    category: {
        'samples': sample_size[category],
        'mean': averages[category],
        'std_dev': std_devs[category],
        'norm_mean': normalized[category],
        'norm_std_dev': std_devs_norm[category],

    }
    for category in attr_counts.keys()
}

print(json.dumps(results, indent=4))

highest_urls = [f"https://mmolb.com/player/{owner}" for owner in highest_star_owners]
print(f"Highest star: {highest_star}")
for owner in highest_urls:
    print(f"    {owner}")