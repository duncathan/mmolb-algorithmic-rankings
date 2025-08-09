from __future__ import annotations

import copy
import itertools
import json
import math
import urllib.request
from bisect import bisect_left
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

import networkx as nx

API = "https://mmolb.com/api/"

@dataclass(unsafe_hash=True)
class Team:
    id: str
    league: str
    name: str

    wins: int
    losses: int
    run_diff: int

    cached_data: dict = field(default_factory=dict, hash=False)

    @property
    def win_diff(self) -> int:
        return self.wins - self.losses

    @property
    def games_remaining(self) -> int:
        return 120 - (self.wins + self.losses)

    @property
    def most_possible_wins(self) -> int:
        return self.wins + self.games_remaining

    def __repr__(self) -> str:
        return f"{self.name} ({self.wins} - {self.losses})"

    def divisional_status(
            self,
            all_teams: Iterable[Team],
            remaining_games: dict[tuple[Team, Team], int],
    ) -> Postseason:
        if "divisional" not in self.cached_data:
            self.cached_data["divisional"] = self._divisional_status(all_teams, remaining_games)
        return self.cached_data["divisional"]

    def _divisional_status(
            self,
            all_teams: Iterable[Team],
            remaining_games: dict[tuple[Team, Team], int],
    ) -> Postseason:
        division = {team for team in all_teams if team.league == self.league}
        division_standings = sorted_teams(division)
        our_standing = division_standings.index(self)
        fake_standings = {team: team.wins for team in division_standings}

        if self.most_possible_wins < division_standings[1].wins:
            # if we can't win more games than #2 already has, there's no hope
            return Postseason.BEIGED

        if self.wins > division_standings[2].most_possible_wins:
            # if we can't *lose* more games than #3 already has, it's guaranteed
            return Postseason.CLINCHED

        if self.wins >= division_standings[1].wins:
            # it may be possible we've clinched?
            return Postseason.CONTENDER # for now
        else:
            # it may be possible we're eliminated?
            division_leader = division_standings[0]
            unhandled_games: dict[tuple[Team, Team], int] = {}

            for (home, away), num_games in remaining_games.items():
                # win em all, baby
                if home == self or away == self:
                    fake_standings[self] += num_games
                    continue

                # treat all interdivision games as losses for other teams in our division
                if (home not in division) or (away not in division):
                    continue

                # since we're assuming we win all remaining games, lower ranked teams
                # can never outplace us making it safe for them to win all their games
                if division_standings.index(home) > our_standing:
                    fake_standings[home] += num_games
                    continue
                if division_standings.index(away) > our_standing:
                    fake_standings[away] += num_games
                    continue

                unhandled_games[(home, away)] = num_games

            if self.can_top_subdivision(unhandled_games, fake_standings):
                # we have a chance to win the division, so def a chance at postseason
                return Postseason.CONTENDER

            old_unhandled = unhandled_games
            unhandled_games = {}

            for (home, away), num_games in old_unhandled.items():
                # #1 is out of reach anyway, so the more wins that #1 gets versus
                # other contenders, the easier it is for us to earn the #2 spot
                if (home == division_leader) or (away == division_leader):
                    fake_standings[division_leader] += num_games
                    continue

                unhandled_games[(home, away)] = num_games

            if self.can_top_subdivision(unhandled_games, fake_standings):
                return Postseason.CONTENDER

            return Postseason.BEIGED


    def clinched_wildcard(
            self,
            all_teams: Iterable[Team],
            remaining_games: dict[tuple[Team, Team], int]
    ) -> Postseason:
        standings = sorted_teams(all_teams)
        our_standing = standings.index(self)

        return Postseason.CONTENDER

    def beiged_wildcard(
            self,
            all_teams: Iterable[Team],
            remaining_games: dict[tuple[Team, Team], int]
    ) -> Postseason:
        # print(self)

        standings = sorted_teams(all_teams)
        our_standing = standings.index(self)
        fake_standings = {team: team.wins for team in standings}

        if self.most_possible_wins < standings[5].wins:
            # if we can't win more games than #6 already has, there's no hope
            return Postseason.BEIGED

        division = {team for team in all_teams if team.league == self.league}
        division_standings = sorted_teams(division)
        division_leaders = division_standings[:2]

        unhandled_games: dict[tuple[Team, Team], int] = {}

        for (home, away), num_games in remaining_games.items():
            # win em all, baby
            if home == self or away == self:
                fake_standings[self] += num_games
                continue

            # since we're assuming we win all remaining games, lower ranked teams
            # can never outplace us making it safe for them to win all their games
            if standings.index(home) > our_standing:
                fake_standings[home] += num_games
                continue
            if standings.index(away) > our_standing:
                fake_standings[away] += num_games
                continue

            # if we're running this code, there's already no possibility that we
            # can be in the top 2 for our division. the more wins they get, the fewer
            # can go to our competitors
            if home in division_leaders:
                fake_standings[home] += num_games
                continue
            if away in division_leaders:
                fake_standings[away] += num_games
                continue

            unhandled_games[(home, away)] = num_games

        if self.can_top_subdivision(unhandled_games, fake_standings):
            # we have a chance to be #3 record overall
            return Postseason.CONTENDER

        # time for evil
        games_to_sim: list[tuple[Team, Team]] = []
        for matchup, games in unhandled_games.items():
            for i in range(games):
                games_to_sim.append(matchup)

        total = math.pow(2, len(games_to_sim))
        for i, possible_results in enumerate(itertools.product((True, False), repeat=len(games_to_sim))):
            faker_standings = copy.copy(fake_standings)

            print(i * 100.0 / float(total))
            for (home, away), home_win in zip(games_to_sim, possible_results, strict=True):
                if home_win:
                    faker_standings[home] += 1
                else:
                    faker_standings[away] += 1

            sorted_this_division = sorted((team for team in faker_standings.keys() if team.league == self.league), key=lambda team: faker_standings[team], reverse=True)
            sorted_other_division = sorted((team for team in faker_standings.keys() if team.league != self.league), key=lambda team: faker_standings[team], reverse=True)

            leaders = {sorted_this_division[0], sorted_this_division[1], sorted_other_division[0], sorted_other_division[1]}
            sorted_wildcards = sorted((team for team in faker_standings.keys() if (team not in leaders)), key=lambda team: faker_standings[team], reverse=True)

            # print({team: faker_standings[team] for team in sorted_wildcards})
            # print()
            if faker_standings[self] >= faker_standings[sorted_wildcards[1]]:
                return Postseason.CONTENDER

        return Postseason.BEIGED


    def postseason_status(
            self,
            all_teams: Iterable[Team],
            remaining_games: dict[tuple[Team, Team], int]
    ) -> Postseason:
        status = self.divisional_status(all_teams, remaining_games)

        if status == Postseason.BEIGED:
            status = self.beiged_wildcard(all_teams, remaining_games)
        if status == Postseason.CONTENDER:
            status = self.clinched_wildcard(all_teams, remaining_games)

        return status


    def can_top_subdivision(self, games: dict[tuple[Team, Team], int], standings: dict[Team, int]) -> bool:
        # print(standings)
        # print(games)

        remaining_games = sum(games.values())

        graph = nx.DiGraph()
        graph.add_node("s")
        graph.add_node("t")

        for matchup, num_games in games.items():
            graph.add_edge("s", matchup, capacity=num_games)
            for team in matchup:
                graph.add_edge(matchup, team)
                graph.add_edge(team, "t", capacity=(standings[self] - standings[team]))

        flow_val, flow_dict = nx.maximum_flow(graph, "s", "t")

        return flow_val >= remaining_games


def sorted_teams(teams: Iterable[Team]) -> list[Team]:
    def tiebreak(team: Team) -> tuple[int, int, str]:
        return team.win_diff, team.run_diff, team.id

    return sorted(teams, key=tiebreak, reverse=True)


class Postseason(Enum):
    BEIGED = 0
    CONTENDER = 1
    CLINCHED = 2



clover_id = "6805db0cac48194de3cd3fe4"
pineapple_id = "6805db0cac48194de3cd3fe5"
season2_id = "6858e7be2d94a56ec8d460ea"

def teams_for_league(league_id: str) -> dict[str, Team]:
    teams: dict[str, Team] = {}

    with urllib.request.urlopen(f"{API}/league/{league_id}") as league_url:
        league = json.load(league_url)
    for team_id in league["Teams"]:
        with urllib.request.urlopen(f"{API}/team/{team_id}") as team_url:
            team_json = json.load(team_url)
        record = team_json["Record"]["Regular Season"]

        team = Team(
            id=team_id,
            name=f"{team_json['Emoji']} {team_json['Location']} {team_json['Name']}",
            league=team_json["League"],
            wins=record["Wins"],
            losses=record["Losses"],
            run_diff=record["RunDifferential"],
        )

        teams[team.id] = team

    return teams

print("clover")
clover = teams_for_league(clover_id)
print("pineapple")
pineapple = teams_for_league(pineapple_id)
all_teams = clover | pineapple

def remaining_schedule(season_id: str) -> dict[tuple[Team, Team], int]:
    remaining_games: dict[tuple[Team, Team], int] = defaultdict(int)

    with urllib.request.urlopen(f"{API}/season/{season_id}") as season_url:
        season = json.load(season_url)

    days: list[str] = season["Days"]
    days_cache: dict[str, dict] = {}

    def is_day_incomplete(day_id: str) -> bool:
        with urllib.request.urlopen(f"{API}/day/{day_id}") as day_url:
            day = json.load(day_url)
        print(day["Day"])
        days_cache[day_id] = day
        return all((game["State"] != "Complete") for game in day["Games"])

    first_unfinished_day = bisect_left(days, True, key=is_day_incomplete)
    print()

    for day_id in days[first_unfinished_day:]:
        if day_id not in days_cache:
            with urllib.request.urlopen(f"{API}/day/{day_id}") as day_url:
                days_cache[day_id] = json.load(day_url)
        day = days_cache[day_id]

        print(day["Day"])
        if any((game["League"] != "Greater") for game in day["Games"]):
            continue
        for game in day["Games"]:
            if game["State"] == "Complete":
                continue
            matchup = (all_teams[game["AwayTeamID"]], all_teams[game["HomeTeamID"]])
            remaining_games[matchup] += 1

    return remaining_games

schedule = remaining_schedule(season2_id)
divisional_status = {team: team.postseason_status(all_teams.values(), schedule) for team in all_teams.values()}

for team, status in divisional_status.items():
    print(f"{team}: {status}")
