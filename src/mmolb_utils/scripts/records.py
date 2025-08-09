import dataclasses
import statistics
from collections import defaultdict

import matplotlib
import matplotlib.cm
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize

from mmolb_utils.apis import cashews


@dataclasses.dataclass
class Record:
    wins: int = 0
    losses: int = 0

    def __repr__(self) -> str:
        return f"{self.wins} - {self.losses}"

    @property
    def diff(self) -> int:
        return self.wins - self.losses

    @property
    def games_played(self) -> int:
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        return float(self.wins) / float(self.games_played)


all_records: dict[str, dict[str, Record]] = defaultdict(lambda: defaultdict(Record))
season_records: dict[str, Record] = defaultdict(Record)

def team_name(team: dict) -> str:
    return f"{team['emoji']} {team['location']} {team['name']}"

id_to_team_name = {team['team_id']: team_name(team) for team in cashews.get_teams()}

for game in cashews.get_games(season=2):
    if not isinstance(game['day'], int):
        continue
    if game['day'] % 2 != 0:
        continue
    if game['day'] > 240:
        continue

    if game['state'] != "Complete":
        continue

    home = game["home_team_id"]
    away = game["away_team_id"]

    status = game['last_update']
    home_win = status["home_score"] > status["away_score"]

    if home_win:
        if game['day'] > 120:
            all_records[home][away].wins += 1
            all_records[away][home].losses += 1
        season_records[home].wins += 1
        season_records[away].losses += 1
    else:
        if game['day'] > 120:
            all_records[home][away].losses += 1
            all_records[away][home].wins += 1
        season_records[home].losses += 1
        season_records[away].wins += 1

all_records = {
    team: dict(sorted(
        ((opponent, record) for opponent, record in records.items()),
        key=lambda it: (it[1].games_played, it[1].wins), reverse=True
    ))
    for team, records in all_records.items()
    if sum(record.games_played for record in records.values()) == 60
}

num_opponents = dict(sorted(
    ((f"{id_to_team_name[team]} ({season_records[team].diff})", len(records))
    for team, records in all_records.items()),
    key=lambda it: (it[1], season_records[it[0]], it[0])
))
values = num_opponents.values()

win_diffs: dict[int, list[int]] = defaultdict(list)
for team, records in all_records.items():
    win_diffs[len(records)].append(abs(season_records[team].diff))
win_diffs_tup: list[tuple[int, list[int]]] = sorted(
    ((num, diff) for num, diff in win_diffs.items()),
    key=lambda it: it[0],
)

average_win_diff = [statistics.mean(diff) for _, diff in win_diffs_tup]
max_win_diff = max(average_win_diff)
min_win_diff = min(average_win_diff)
viridis = matplotlib.colormaps.get_cmap("viridis")
norm = Normalize(min_win_diff, max_win_diff, True)

mean = statistics.mean(values)
std_dev = statistics.stdev(values)
median = statistics.median(values)
mode = statistics.mode(values)

print(num_opponents)
print(f"Average num opponents: {mean}")

N, bins, patches = plt.hist(values, bins=len(set(values)), edgecolor='black', alpha=0.7)

win_diff_colors = viridis([norm(diff) for diff in average_win_diff])
for i in range(len(patches)):
    patches[i].set_facecolor(win_diff_colors[i])

plt.xlabel("# Unique Opponents")
plt.ylabel("Occurences")

# plt.axvline(mean, color='red', label=f"Mean: {mean:.2f}")
plt.axvline(median, color='red', label=f"Median: {median}")
plt.axvline(mode, color='cyan', label=f"Mode: {mode}")
plt.axvline(mean - std_dev, color='magenta', label=f"Standard Deviation: {std_dev:.2f}")
plt.axvline(mean + std_dev, color='magenta')

plt.legend()

plt.show()
