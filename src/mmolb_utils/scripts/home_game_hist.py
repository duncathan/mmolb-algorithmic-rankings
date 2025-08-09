from collections import defaultdict
import dataclasses
import functools
import statistics

from matplotlib import pyplot as plt
import matplotlib
import matplotlib.cm
from matplotlib.colors import LogNorm, Normalize

from mmolb_utils.apis import cashews

@functools.total_ordering
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
    
    def __lt__(self, other: "Record") -> bool:
        return self.diff < other.diff


all_records: dict[str, dict[str, Record]] = defaultdict(lambda: defaultdict(Record))
home_vs_away: dict[str, Record] = defaultdict(Record)

def team_name(team: dict) -> str:
    return f"{team['emoji']} {team['location']} {team['name']}"

id_to_team_name = {team['team_id']: team_name(team) for team in cashews.get_teams()}

for game in cashews.get_games(season=3):
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

    home_vs_away[home].wins += 1
    home_vs_away[away].losses += 1

home_rate = {team: record.win_rate for team, record in home_vs_away.items() if record.games_played >= 60}
home_rate = {team: record for team, record in sorted(home_rate.items(), key=lambda it: it[1])}
values = home_rate.values()

print("bottom 10")
print(list(home_rate.items())[:10])

print("top 10")
print(list(home_rate.items())[-10:])



# win_diffs: dict[int, list[int]] = defaultdict(list)
# for team, records in all_records.items():
#     win_diffs[len(records)].append(abs(home_vs_away[team].diff))
# win_diffs_tup: list[tuple[int, list[int]]] = sorted(((num, diff) for num, diff in win_diffs.items()), key=lambda it: it[0])

# average_win_diff = [statistics.mean(diff) for _, diff in win_diffs_tup]
# max_win_diff = max(average_win_diff)
# min_win_diff = min(average_win_diff)
# viridis = matplotlib.colormaps.get_cmap("viridis")
# norm = Normalize(min_win_diff, max_win_diff, True)

mean = statistics.mean(values)
std_dev = statistics.stdev(values)
median = statistics.median(values)
mode = statistics.mode(values)

# print(home_rate)
# print(f"Average num opponents: {mean}")

N, bins, patches = plt.hist(values, color='green', edgecolor='black', alpha=0.7)

# win_diff_colors = viridis([norm(diff) for diff in average_win_diff])
# for i in range(len(patches)):
#     patches[i].set_facecolor(win_diff_colors[i])

plt.xlabel("% Home Games")
plt.ylabel("Occurences")

# plt.axvline(mean, color='red', label=f"Mean: {mean:.2f}")
plt.axvline(median, color='red', label=f"Median: {median}")
plt.axvline(mode, color='cyan', label=f"Mode: {mode}")
plt.axvline(mean - std_dev, color='magenta', label=f"Standard Deviation: {std_dev:.2f}")
plt.axvline(mean + std_dev, color='magenta')

plt.legend()

plt.show()