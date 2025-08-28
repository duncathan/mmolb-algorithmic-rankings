from mmolb_utils.apis.cashews.stats_api import StatKey
from mmolb_utils.lib.stats.operations import RawStat

# raw stats

Appearances = RawStat(StatKey.Appearances)
App = Appearances
"""Appearances"""

BattersFaced = RawStat(StatKey.BattersFaced)
BF = BattersFaced
"""Batters faced"""

BlownSaves = RawStat(StatKey.BlownSaves)
BS = BlownSaves
"""Blown saves"""

CompleteGames = RawStat(StatKey.CompleteGames)
CG = CompleteGames
"""Complete games"""

EarnedRuns = RawStat(StatKey.EarnedRuns)
ER = EarnedRuns
"""Earned runs"""

GamesFinished = RawStat(StatKey.GamesFinished)
GF = GamesFinished
"""Games finished"""

Starts = RawStat(StatKey.Starts)
GS = Starts
"""Games started"""

HitBatters = RawStat(StatKey.HitBatters)
HB = HitBatters
"""Hit batters"""

HitsAllowed = RawStat(StatKey.HitsAllowed)
H = HitsAllowed
"""Hits allowed"""

HomeRunsAllowed = RawStat(StatKey.HomeRunsAllowed)
HR = HomeRunsAllowed
"""Home runs allowed"""

InheritedRunners = RawStat(StatKey.InheritedRunners)
IR = InheritedRunners
"""Inherited runners"""

InheritedRunsAllowed = RawStat(StatKey.InheritedRunsAllowed)

Losses = RawStat(StatKey.Losses)
"""Pitcher losses"""
L = Losses
"""Pitcher losses"""

MoundVisits = RawStat(StatKey.MoundVisits)

NoHitters = RawStat(StatKey.NoHitters)

Outs = RawStat(StatKey.Outs)
"""Pitcher outs"""

PerfectGames = RawStat(StatKey.PerfectGames)

PitchesThrown = RawStat(StatKey.PitchesThrown)
PT = PitchesThrown
"""Pitches thrown"""
NumberOfPitches = PitchesThrown
"""(Pitches thrown)"""
NP = PitchesThrown
"""Number of pitches (pitches thrown)"""

QualityStart = RawStat(StatKey.QualityStarts)
QS = QualityStart
"""QualityStart"""

Saves = RawStat(StatKey.Saves)
SV = Saves
"""Saves"""

Shutouts = RawStat(StatKey.Shutouts)
SHO = Shutouts
"""Shutouts"""

Strikeouts = RawStat(StatKey.Strikeouts)
"""Pitcher strikeouts"""
SO = Strikeouts
"""Pitcher strikeouts"""
K = Strikeouts
"""Pitcher strikeouts"""

UnearnedRuns = RawStat(StatKey.UnearnedRuns)
UER = UnearnedRuns
"""Unearned runs"""

Walks = RawStat(StatKey.Walks)
"""Pitcher walks / bases on balls"""
BB = Walks
"""Pitcher walks / bases on balls"""

Wins = RawStat(StatKey.Wins)
W = Wins
"""Pitcher wins"""

# basic calculated stats

IP = Outs / 3
"""Innings pitched"""

ERA = 9 * ER / IP
"""Earned run average"""

SVpct = SV / (SV + BS)
"""Save percentage"""

WHIP = (BB + H) / IP
"""Walks and hits per inning pitched"""

Wpct = W / (W + L)
"""Pitcher winning percentage"""

# advanced stats

# TODO: FIP

H_per_9 = 9 * H / IP
"""Hits per nine innings"""

HR_per_9 = 9 * HR / IP
"""Home runs per nine innings"""

Kpct = K / BF
"""Strikeout percentage"""

K_per_9 = 9 * K / IP
"""Strikeouts per nine innings"""

K_per_BB = K / BB
"""Strikeout to walk ratio"""

BB_per_9 = 9 * BB / IP
"""Walks per nine innings"""

BBpct = BB / BF
"""Walk rate"""
