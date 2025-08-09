from mmolb_utils.apis import cashews, mmolb

players_with_item: list[str] = []

player_ids = [player['data']['_id'] for player in cashews.get_entities(cashews.EntityKind.PlayerLite) if player['data']['SeasonStats']]

for player in mmolb.get_players(*player_ids):
    shoes = player['Equipment']['Feet']
    if shoes is None:
        continue
    if not shoes['Prefixes'] or any(prefix != "Avaricious" for prefix in shoes['Prefixes']):
        continue
    if not shoes['Suffixes'] or any(suffix != "of Fortune" for suffix in shoes['Suffixes']):
        continue
    players_with_item.append(f"https://mmolb.com/player/{player['_id']}")

for player in players_with_item:
    print(player)
