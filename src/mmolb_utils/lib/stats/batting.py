from mmolb_utils.apis.cashews.stats_api import StatKey
from mmolb_utils.lib.stats.operations import RawStat, StatTarget

# raw stats

AtBats = RawStat(StatKey.AtBats)
AB = AtBats
"""At-bats"""

CaughtDoublePlay = RawStat(StatKey.CaughtDoublePlay)
CDP = CaughtDoublePlay
"""Caught double play"""

CaughtStealing = RawStat(StatKey.CaughtStealing)
CS = CaughtStealing
"""Caught stealing"""

Doubles = RawStat(StatKey.Doubles)
_2B = Doubles
"""Doubles"""

FieldOuts = RawStat(StatKey.FieldOut)

FieldersChoice = RawStat(StatKey.FieldersChoice)

Flyouts = RawStat(StatKey.Flyouts)
FO = Flyouts
"""Flyouts"""

ForceOuts = RawStat(StatKey.ForceOuts)
F = ForceOuts
"""Force outs"""

GroundedIntoDoublePlay = RawStat(StatKey.GroundedIntoDoublePlay)
GIDP = GroundedIntoDoublePlay
"""Grounded into double play"""

GroundOuts = RawStat(StatKey.Groundouts)
GO = GroundOuts
"""Ground outs"""

HitByPitch = RawStat(StatKey.HitByPitch)
HBP = HitByPitch
"""Hit by pitch"""

HomeRuns = RawStat(StatKey.HomeRuns)
HR = HomeRuns
"""Home runs"""

LeftOnBase = RawStat(StatKey.LeftOnBase)
LOB = LeftOnBase
"""Left on base"""

LineOuts = RawStat(StatKey.Lineouts)
LO = LineOuts
"""Line outs"""

PlateAppearances = RawStat(StatKey.PlateAppearances)
PA = PlateAppearances
"""Plate appearances"""

PopOuts = RawStat(StatKey.Popouts)
PO = PopOuts
"""Pop outs"""

ReachedOnError = RawStat(StatKey.ReachedOnError)
ROE = ReachedOnError
"""Reached on error"""

Runs = RawStat(StatKey.Runs)
R = Runs
"""Runs"""

RunsBattedIn = RawStat(StatKey.RunsBattedIn)
RBI = RunsBattedIn
"""Runs batted in"""

SacFlies = RawStat(StatKey.SacFlies)
SF = SacFlies
"""Sacrifice flies"""

SacDoublePlays = RawStat(StatKey.SacrificeDoublePlays)
SDP = SacDoublePlays
"""Sacrifice double plays"""

Singles = RawStat(StatKey.Singles)
_1B = Singles
"""Singles"""

StolenBases = RawStat(StatKey.StolenBases)
SB = StolenBases
"""Stolen bases"""

StruckOut = RawStat(StatKey.StruckOut)
"""Batter strikeouts"""
Strikeouts = StruckOut
"""Batter strikeouts"""
SO = StruckOut
"""Batter strikeouts"""
K = StruckOut
"""Batter strikeouts"""

Triples = RawStat(StatKey.Triples)
_3B = Triples
"""Triples"""

Walked = RawStat(StatKey.Walked)
"""Batter walks / bases on balls"""
Walks = Walked
"""Batter walks / bases on balls"""
BB = Walked
"""Batter walks / bases on balls"""

# basic calculated stats

Hits = _1B + _2B + _3B + HR
H = Hits
"""Hits"""

AVG = H / AB
"""Batting average"""
BA = AVG
"""Batting average"""

OBP = (H + BB + HBP) / PA
"""On-base percentage"""

TotalBases = _1B * 1 + _2B * 2 + _3B * 3 + HR * 4
TB = TotalBases
"""Total bases"""

SLG = TB / AB
"""Slugging percentage"""

OPS = OBP + SLG
"""On-base plus slugging"""

wOPS = OBP * 1.7 + SLG
"""Weighted on-base plus slugging (`OBP * 1.7 + SLG`)"""

XBH = _2B + _3B + HR
"""Extra-base hits"""

AirOuts = FO + LO + PO
AO = AirOuts
"""Air outs"""

SB_pct = SB / (SB + CS)
"""Stolen base percentage"""

Kpct = K / PA
"""Strikeout percentage"""

BBpct = BB / PA
"""Walk percentage"""

# advanced stats

BABIP = (H - HR) / (AB - K - HR + SF)
"""Batting average on balls in play"""

ISO = SLG - AVG
"""Isolated power"""

basicRunsCreated = TB * (H + BB) / (AB + BB)
bRC = basicRunsCreated
"""A basic measure of runs created"""


if __name__ == "__main__":
    print("BABIP")
    print(BABIP.evaluate_all(StatTarget.Player, season=5, filters=StatKey.AtBats > 40))  # 0.8343479553670636

    print("Player")
    print(OPS.evaluate_individual(StatTarget.Player, "6840fd16925dd4f9d72abc94", season=5))  # 0.8343479553670636
    # print("Team")
    # print(OPS.evaluate_individual(StatTarget.Team, "6807b2e564804c8548d0e787", season=5))
    # print("League")
    # print(OPS.evaluate_individual(StatTarget.League, "6805db0cac48194de3cd3feb", season=5))
    print("TeamAgainst")
    print(OPS.evaluate_individual(StatTarget.TeamAgainst, "6807b2e564804c8548d0e787", season=5))

    for team, ops_against in sorted(
        OPS.evaluate_all(StatTarget.TeamAgainst, season=5, filters=StatKey.PlateAppearances > 40 * 9 * 3).items(),
        key=lambda it: it[1],
        reverse=True,
    ):
        print(f"{team} - {ops_against:0.3f}")
