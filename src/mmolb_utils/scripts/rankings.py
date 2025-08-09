import json
import time
import urllib
import urllib.request
from math import floor

import glicko2
import pandas as pd

glicko2.Player._tau = 0.3

# if not sys.stdout.isatty():
#     sys.stdout = codecs.getwriter('utf8')(sys.stdout)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', None)

players = pd.read_csv("https://freecashe.ws/api/allplayers/csv?fields=TeamID,Birthday")

# collect team data
teams = pd.read_json("https://freecashe.ws/api/allteams", orient='index')
teams["FullName"] = teams.apply(lambda team: f"{team["Emoji"]} {team["Location"]} {team["Name"]}", axis='columns')
teams = teams.loc[teams["Record"] != {"Regular Season": {"Losses": 0, "RunDifferential": 0, "Wins": 0}}]
teams["Games Played (team API)"] = teams["Record"].map(lambda record: record["Regular Season"]["Wins"] + record["Regular Season"]["Losses"])
teams["Record (team API)"] = teams["Record"].map(lambda record: f'{record["Regular Season"]["Wins"]}-{record["Regular Season"]["Losses"]}')

def keyfunc(x):
    if x == "Preseason":
        return 0
    if x == "Superstar Break":
        return 60
    return int(x)

teams["Birthday"] = teams.apply(lambda team: min(players.loc[players["TeamID"] == team["_id"]]["Birthday"], key=keyfunc), axis='columns')

# collect game data
games = pd.read_json("https://freecashe.ws/api/games")
games["timestamp"] = games.apply(lambda row: (row["season"], row["day"]), axis='columns')
games["home_team_win"] = games["home_score"] >= games["away_score"]
games["away_team_win"] = games["away_score"] >= games["home_score"]
mask = (games["home_team_win"] == True)
games.loc[mask, "winner_id"] = games.loc[mask]["home_team_id"]
games.loc[~mask, "winner_id"] = games.loc[~mask]["away_team_id"]
current_day = max(games["timestamp"])

npc_team_mask = (games["state"] == '')
mask2 = (teams["_id"] == '')
npc_teams = (
    '6805db0cac48194de3cd4127',
    '6805db0dac48194de3cd413a',
    '6805db0dac48194de3cd414d',
    '6805db0dac48194de3cd4160',
    '6805db0dac48194de3cd4173',
    '6805db0dac48194de3cd4186',
    '6805db0dac48194de3cd4199',
    '6805db0dac48194de3cd41ac',
    '6805db0dac48194de3cd41bf',
    '6805db0dac48194de3cd41d2',
    '6805db0dac48194de3cd41e5',
    '6805db0dac48194de3cd41f8',
    '6805db0dac48194de3cd420b',
    '6805db0dac48194de3cd421e',
    '6805db0dac48194de3cd4231',
    '6805db0dac48194de3cd4244',
)
for team in npc_teams:
    mask2 |= (teams["_id"] == team)
    npc_team_mask |= (games["home_team_id"] == team) | (games["away_team_id"] == team)

games = games.loc[npc_team_mask]
teams = teams.loc[mask2]
games = games.loc[games["home_team_id"] != games["away_team_id"]]

should_refresh_time = time.time() + 60 * 3

count = 0
def get_current_game_state(old_game):
    print(old_game['game_id'])
    global count
    count += 1
    with urllib.request.urlopen(f"https://mmolb.com/api/game/{old_game['game_id']}") as url:
        game = json.load(url)
    if game["State"] != "Complete":
        return old_game

    new_game = old_game.copy()
    new_game["home_score"] = game["EventLog"][-1]["home_score"]
    new_game["away_score"] = game["EventLog"][-1]["away_score"]
    new_game["last_update"] = floor(time.time() * 1000)
    new_game["state"] = game["State"]
    new_game["home_team_win"] = new_game["home_score"] >= new_game["away_score"]
    new_game["away_team_win"] = new_game["away_score"] >= new_game["home_score"]
    return new_game

potential_desynced_cond = (games["state"] != "Complete") & ((games["last_update"] / 1000.0) < should_refresh_time)
games.loc[potential_desynced_cond] = games.loc[potential_desynced_cond].apply(get_current_game_state, axis='columns')
print(f"API calls: {count}")
print()

# print(current_day)
# games = games.loc[games["timestamp"] != current_day]
games = games.loc[games["state"] == "Complete"]

games["home_team_win"] = games["home_score"] >= games["away_score"]
games["away_team_win"] = games["away_score"] >= games["home_score"]

# teams["WinsByGameAPI"] = teams["_id"].map(lambda _id: len(games.loc[games["winner_id"] == _id]))
# teams["LossesByGameAPI"] = teams["_id"].map(lambda _id: len(games.loc[games["winner_id"] != _id]))

teams["WinsByGameAPI"] = teams["_id"].map(lambda _id: len(games.loc[(games["home_team_id"] == _id) & (games["winner_id"] == _id)]))
teams["WinsByGameAPI"] += teams["_id"].map(lambda _id: len(games.loc[(games["away_team_id"] == _id) & (games["winner_id"] == _id)]))
teams["LossesByGameAPI"] = teams["_id"].map(lambda _id: len(games.loc[(games["home_team_id"] == _id) & (games["winner_id"] != _id)]))
teams["LossesByGameAPI"] += teams["_id"].map(lambda _id: len(games.loc[(games["away_team_id"] == _id) & (games["winner_id"] != _id)]))

teams["Record (games API)"] = teams.apply(lambda team: f'{team["WinsByGameAPI"]}-{team["LossesByGameAPI"]}', axis='columns')
teams["Games Played (games API)"] = teams["WinsByGameAPI"] + teams["LossesByGameAPI"]

missing_games_cond = (teams["Record (team API)"] != teams["Record (games API)"])

# count = 0
# def get_current_record(old_team):
#     print(old_team["_id"])
#     global count
#     count += 1
#     with urllib.request.urlopen(f"https://mmolb.com/api/team/{old_team['_id']}") as url:
#         team = json.load(url)
#     return team["Record"]


# teams.loc[missing_games_cond, 'Record'] = teams.loc[missing_games_cond].apply(get_current_record, axis='columns')
# print(f"API calls: {count}")
# print()

# teams["Games Played (team API)"] = teams["Record"].map(lambda record: record["Regular Season"]["Wins"] + record["Regular Season"]["Losses"])
# teams["Record (team API)"] = teams["Record"].map(lambda record: f'{record["Regular Season"]["Wins"]}-{record["Regular Season"]["Losses"]}')

teams_with_missing_games = teams.loc[missing_games_cond]

print(teams_with_missing_games[['FullName', 'Birthday', "Games Played (team API)", "Record (team API)", "Games Played (games API)", "Record (games API)"]])
# assert False

# games["timestamp"] = games.apply(lambda row: (row["season"], row["day"]), axis='columns')
# games["home_team_win"] = games["home_score"] > games["away_score"]
# games["league"] = games["home_team_id"].map(lambda team: teams.loc[team]["League"])

# ALL_LEAGUES = teams["League"].unique().tolist()
# # ALL_LEAGUES = ["6805db0cac48194de3cd3ff3"]

# for league_id in ALL_LEAGUES:
#     league = pd.read_json(f"https://mmolb.com/api/league/{league_id}").iloc[0]
#     print(f"{league["Emoji"]} {league["Name"]} League ({league["LeagueType"]})")

#     league_games = games.loc[games["league"] == league_id]

#     # latest_game = league_games.iloc[-1]["timestamp"]
#     # if any(state != "Complete" for state in league_games.loc[league_games["timestamp"] == latest_game]["state"]):
#     #     league_games = league_games.loc[league_games["timestamp"] < latest_game]

#     league_teams = teams.loc[teams["League"] == league_id]

#     league_ratings = pd.DataFrame(index=league_teams.index)
#     league_ratings["_id"] = league_teams.index
#     league_ratings["name"] = league_teams.index.map(lambda idx: team_name(idx))

#     # basic record
#     league_ratings["wins"] = league_teams["Record"].map(lambda record: record["Regular Season"]["Wins"])
#     league_ratings["losses"] = league_teams["Record"].map(lambda record: record["Regular Season"]["Losses"])
#     league_ratings["run_diff"] = league_teams["Record"].map(lambda record: record["Regular Season"]["RunDifferential"])
#     league_ratings["win_diff"] = league_ratings["wins"] - league_ratings["losses"]

#     # # glicko
#     # glicko_model = Glicko2Estimator(
#     #     key1_field="home_team_id",
#     #     key2_field="away_team_id",
#     #     timestamp_field="timestamp",
#     #     initial_time=(0, 0),
#     # ).fit(games, games["home_team_win"])

#     # glicko_est = glicko_model.rating_model.to_frame()
#     # glicko_est["visible_rating"] = glicko_est["rating"].map(lambda rating: rating[0])

#     # glicko_pivoted = glicko_est.pivot_table(index='valid_from', columns='key', values='visible_rating')
#     # glicko_pivoted.ffill(axis='index', inplace=True)

#     # league_ratings["glicko2"] = glicko_pivoted.iloc[-1]

#     # glicko_est["modified_rating"] = glicko_est["rating"].map(lambda rating: rating[0] - (rating[1] * 2 * rating[2] / 0.06))

#     # glicko_pivoted = glicko_est.pivot_table(index='valid_from', columns='key', values='modified_rating')
#     # glicko_pivoted.ffill(axis='index', inplace=True)

#     # league_ratings["glicko2-mod"] = glicko_pivoted.iloc[-1]

#     # # elo
#     # elo_model = EloEstimator(
#     #     key1_field="home_team_id",
#     #     key2_field="away_team_id",
#     #     timestamp_field="timestamp",
#     #     initial_time=(0, 0),
#     # ).fit(games, games["home_team_win"])

#     # elo_est = elo_model.rating_model.to_frame()
#     # elo_pivoted = elo_est.pivot_table(index='valid_from', columns='key', values='rating')
#     # elo_pivoted.ffill(axis='index', inplace=True)

#     # league_ratings["elo"] = elo_pivoted.iloc[-1]

#     def get_sorted(data):
#         return data.apply(lambda row: f"{row['name']} ({row['wins']}-{row['losses']}, {row['win_diff']:+} W, {row['run_diff']:+} R)", axis='columns').values

#     default_sort = league_ratings.sort_values(by=['wins', 'run_diff', '_id'], ascending=False)
#     alt_sort = league_ratings.sort_values(by=['wins', 'win_diff', 'run_diff', '_id'], ascending=False)
#     alt2_sort = league_ratings.sort_values(by=['win_diff', 'wins', 'run_diff', '_id'], ascending=False)



#     # elo_sort = league_ratings.sort_values(by='elo', ascending=False)
#     # elo_sorted = elo_sort.apply(lambda row: f"{row['name']} ({row['wins']}-{row['losses']}, {row['elo']:.3f})", axis='columns').values
#     # glicko_sort = league_ratings.sort_values(by='glicko2', ascending=False)
#     # glicko_sorted = glicko_sort.apply(lambda row: f"{row['name']} ({row['wins']}-{row['losses']}, {row['glicko2']:.3f})", axis='columns').values
#     # glickomod_sort = league_ratings.sort_values(by='glicko2-mod', ascending=False)
#     # glickomod_sorted = glickomod_sort.apply(lambda row: f"{row['name']} ({row['wins']}-{row['losses']}, {row['glicko2-mod']:.3f})", axis='columns').values

#     comparison = pd.DataFrame(data={"Wins > Run Diff": get_sorted(default_sort), "Wins > Win Diff > Run Diff": get_sorted(alt_sort), "Win Diff > Wins > Run Diff": get_sorted(alt2_sort)})
#     comparison.index += 1
#     comparison.index.name = "Rank"

#     print(comparison)
#     print()
#     print()
