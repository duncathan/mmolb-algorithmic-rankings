from mmolb_utils.apis.cashews.stats_api import StatKey
from mmolb_utils.lib.stats.operations import RawStat

# raw stats

AllowedStolenBases = RawStat(StatKey.AllowedStolenBases)
ASB = AllowedStolenBases
"""Allowed stolen bases"""

Assists = RawStat(StatKey.Assists)
A = Assists
"""Assists"""

DoublePlays = RawStat(StatKey.DoublePlays)
DP = DoublePlays
"""Double plays"""

Errors = RawStat(StatKey.Errors)
E = Errors
"""Errors"""

Putouts = RawStat(StatKey.Putouts)
PO = Putouts
"""Putouts"""

RunnersCaughtStealing = RawStat(StatKey.RunnersCaughtStealing)
RCS = RunnersCaughtStealing
"""Runners caught stealing"""

# basic calculated stats

RCSpct = RCS / (RCS + ASB)
"""Runners caught stealing percentage"""
