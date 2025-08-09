import itertools
import urllib.request, json

import networkx as nx
from networkx.algorithms.approximation import traveling_salesman_problem

interests = nx.DiGraph()
next_page = ...

page_num = 0
count_per_page = 1000

while next_page is not None:
    url = f"https://freecashe.ws/api/chron/v0/entities?kind=player_lite&count={count_per_page}"
    if next_page is not ...:
        url = f"{url}&page={next_page}"
    
    with urllib.request.urlopen(url) as page:
        players = json.load(page)
    
    next_page = players["next_page"]
    for player in players["items"]:
        if any((mod["Name"] == "Relegated") for mod in player["data"]["Modifications"]):
            continue
        interests.add_edge(player["data"]["Likes"], player["data"]["Dislikes"], player=player["entity_id"])
    
    page_num += 1
    print(f"Processed {page_num * count_per_page} players...")

largest = max(nx.strongly_connected_components(interests), key=len)
connected_interests = interests.subgraph(largest)

print("Solving TSP...")

path = traveling_salesman_problem(connected_interests)

print("Solved")

players = []

for n1, n2 in itertools.pairwise(path):
    players.append(interests.edges[n1, n2]["player"])

print(players)