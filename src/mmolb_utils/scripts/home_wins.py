import dataclasses

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

total_record = Record()

for game in cashews.get_games(season=3):
    if game['state'] != "Complete":
        continue

    # if game['day'] > 12:
    #     continue

    status = game['last_update']
    home_win = status["home_score"] > status["away_score"]

    if home_win:
        total_record.wins += 1
    else:
        total_record.losses += 1

# print(total_record)
print(f"{total_record} ({total_record.win_rate*100:.02f}%)")
