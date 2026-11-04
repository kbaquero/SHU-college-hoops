"""Pool settings. Edit these if the commissioner changes anything."""

SEASON = 2027          # ESPN labels seasons by the year they end (2026-27 -> 2027)
SALARY_CAP = 100
POWER5 = ["ACC", "B10", "B12", "BE", "SEC"]
TEAMS_PER_ENTRY = 10

# Scoring table
PTS_NONCONF_WIN = 1
PTS_CONF_WIN = 2
PTS_CONF_TOURNEY_WIN = 2
PTS_CONF_TOURNEY_CHAMP = 5
PTS_SEED = {1: 8, 2: 6, 3: 6, 4: 6, 5: 4, 6: 4, 7: 4, 8: 4}   # 9-16 -> PTS_SEED_DEFAULT
PTS_SEED_DEFAULT = 2
PTS_NCAA_ROUND = {      # points for a WIN in that round
    "playin": 2,        # footnote: play-in / opening-round games count as a Round of 64 win
    "r64": 2,
    "r32": 4,
    "s16": 6,
    "e8": 8,
    "f4": 10,
    "final": 12,
}

# Footnote: "win data sourced from the official NCAA website". If the commissioner says
# wins over non-Division I opponents don't count, set this to False.
COUNT_NON_D1_WINS = True

# How ESPN labels NCAA tournament rounds in game notes. Checked in order; first match wins.
# If the expanded 76-team field uses new names, add them here (the page will flag
# any NCAA game whose round it couldn't recognise).
NCAA_ROUND_PATTERNS = [
    ("final", r"national championship|championship game"),
    ("f4", r"final four|national semifinal"),
    ("e8", r"elite (8|eight)|regional final"),
    ("s16", r"sweet (16|sixteen)|regional semifinal"),
    ("r32", r"2nd round|second round|round of 32"),
    ("r64", r"1st round|first round|round of 64"),
    ("playin", r"first four|opening round|play-?in|round of 76"),
]
NCAA_PATTERN = r"men's basketball championship|ncaa tournament|ncaa men's|first four|march madness"
NON_NCAA_POSTSEASON = r"\bnit\b|national invitation|\bcbi\b|crown|\bcit\b"

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
