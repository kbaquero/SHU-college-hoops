"""Turn a team's game list into pool points."""
import re

from . import config as C

CONF_FINAL = re.compile(r"(?<!semi)(?<!quarter)(?<!semi-)(?<!quarter-)final\b|championship", re.I)


def ncaa_round(headline):
    h = headline.lower()
    for key, pat in C.NCAA_ROUND_PATTERNS:
        if re.search(pat, h):
            return key
    return None


def classify(g, my_conf, conf_of):
    """Label one game: nonconf | conf | conf_tourney | ncaa | other_post."""
    h = (g.get("headline") or "").lower()
    opp_conf = conf_of.get(g["opp_id"])
    same_conf = opp_conf is not None and opp_conf == my_conf
    if re.search(C.NCAA_PATTERN, h) and not re.search(C.NON_NCAA_POSTSEASON, h):
        return "ncaa"
    if g["season_type"] == 3:
        if re.search(C.NON_NCAA_POSTSEASON, h):
            return "other_post"
        return "conf_tourney" if same_conf else "other_post"
    # Some conference tournaments get filed as regular season; catch them by name + month
    if same_conf and "tournament" in h and g["date"][5:7] in ("02", "03"):
        return "conf_tourney"
    if g.get("conf_flag") is True:
        return "conf"
    if g.get("conf_flag") is False:
        return "nonconf"
    return "conf" if same_conf else "nonconf"


def game_points(kind, won, round_=None, headline="", opp_is_d1=True):
    """Pool points for one finished game, from its type and result (used for evening score previews)."""
    if not won:
        return 0
    if kind == "nonconf":
        return C.PTS_NONCONF_WIN if (C.COUNT_NON_D1_WINS or opp_is_d1) else 0
    if kind == "conf":
        return C.PTS_CONF_WIN
    if kind == "conf_tourney":
        return C.PTS_CONF_TOURNEY_WIN + (C.PTS_CONF_TOURNEY_CHAMP if CONF_FINAL.search(headline or "") else 0)
    if kind == "ncaa":
        return C.PTS_NCAA_ROUND.get(round_ or ncaa_round(headline or ""), 0)
    return 0


def seed_points(seed):
    return C.PTS_SEED.get(seed, C.PTS_SEED_DEFAULT)


def score_team(team, games, conf_of, d1_ids, manual_seed=None):
    """Return a breakdown dict for one pool team."""
    my_conf = team["conf"]
    b = {"nonconf_w": 0, "nonconf_l": 0, "conf_w": 0, "conf_l": 0, "ct_w": 0, "ct_l": 0,
         "ct_champ": False, "seed": manual_seed, "ncaa_w": [], "ncaa_out": False, "w": 0, "l": 0,
         "pts_reg": 0, "pts_ct": 0, "pts_ncaa": 0, "total": 0, "games": [], "warnings": []}
    ct_games, ncaa_seen = [], False
    for g in games:
        kind = classify(g, my_conf, conf_of)
        pts = 0
        if g["completed"]:
            w = g["won"]
            b["w" if w else "l"] += 1
            if kind == "nonconf":
                b["nonconf_w" if w else "nonconf_l"] += 1
                if w and (C.COUNT_NON_D1_WINS or g["opp_id"] in d1_ids):
                    pts = C.PTS_NONCONF_WIN
                b["pts_reg"] += pts
            elif kind == "conf":
                b["conf_w" if w else "conf_l"] += 1
                pts = C.PTS_CONF_WIN if w else 0
                b["pts_reg"] += pts
            elif kind == "conf_tourney":
                b["ct_w" if w else "ct_l"] += 1
                pts = C.PTS_CONF_TOURNEY_WIN if w else 0
                b["pts_ct"] += pts
                ct_games.append(g)
            elif kind == "ncaa":
                ncaa_seen = True
                if b["seed"] is None and g.get("seed"):
                    try:
                        b["seed"] = int(g["seed"])
                    except (TypeError, ValueError):
                        pass
                rnd = ncaa_round(g["headline"])
                if w:
                    if rnd is None:
                        b["warnings"].append(f"{team['team']}: NCAA win on {g['date']} with unrecognised round "
                                             f"'{g['headline']}' - add it to NCAA_ROUND_PATTERNS in config.py")
                    else:
                        pts = C.PTS_NCAA_ROUND[rnd]
                        b["ncaa_w"].append(rnd)
                else:
                    b["ncaa_out"] = True
                b["pts_ncaa"] += pts
        b["games"].append({**g, "kind": kind, "pts": pts,
                           "round": ncaa_round(g.get("headline") or "") if kind == "ncaa" else None})

    # Conference tournament title: won the final (by label), or won out and has since reached the NCAAs
    if ct_games:
        last = ct_games[-1]
        if last["won"] and b["ct_l"] == 0:
            if CONF_FINAL.search(last.get("headline") or "") or ncaa_seen:
                b["ct_champ"] = True
                b["pts_ct"] += C.PTS_CONF_TOURNEY_CHAMP
                last_rec = next(x for x in b["games"] if x["id"] == last["id"])
                last_rec["pts"] += C.PTS_CONF_TOURNEY_CHAMP

    if b["seed"] is not None:
        b["pts_ncaa"] += seed_points(b["seed"])
    elif ncaa_seen:
        b["warnings"].append(f"{team['team']}: in the NCAA tournament but no seed found - add it to data/seeds.csv")

    b["total"] = b["pts_reg"] + b["pts_ct"] + b["pts_ncaa"]
    return b
