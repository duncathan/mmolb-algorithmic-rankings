from mmolb_utils.apis.cashews import get_teams
from mmolb_utils.apis.mmolb import get_players, get_simple_endpoint

equipment: list[dict] = []

for i, cash_team in enumerate(get_teams()):
    if i > 10:
        break
    print(i)
    team = get_simple_endpoint("team", cash_team['team_id'])
    equipment.extend(team.get('Inventory', []))
    player_ids = [team_player['PlayerID'] for team_player in team['Players']]
    for player in get_players(*player_ids):
        equipment.extend(player['Equipment'].values())

print(equipment)