"""Daily update: pull results, score every entry, write docs/data.json + docs/index.html.

Usage:  python -m tracker.run            (normal run against ESPN)
"""
import json, sys, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from . import config as C, espn
from .teams import load_teams, save_teams, resolve_espn_ids, load_entries, load_seeds
from .scoring import score_team
from .render import render_html

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def _pts_pair(score):
    try:
        a, b = (int(x) for x in score.split("-"))
        return a, b
    except (ValueError, AttributeError):
        return None, None


def todays_games(results, owners, today):
    """Pool teams' games on `today` (an Eastern date), one row per game even when both teams are picked."""
    games = {}
    for team, b in results.items():
        for g in b.get("games", []):
            if g.get("date") != today:
                continue
            row = games.setdefault(g["id"], {
                "id": g["id"], "start": g.get("start", ""), "tbd": bool(g.get("time_tbd")),
                "tv": g.get("tv", ""), "neutral": bool(g.get("neutral")), "completed": g["completed"],
                "kind": g.get("kind", ""), "sides": {}})
            mine, theirs = _pts_pair(g.get("score", ""))
            row["sides"][team] = {"pool": True, "home": bool(g.get("home")), "owners": owners.get(team, []),
                                  "won": g.get("won"), "score": g.get("score", ""), "opp": g.get("opp_name", ""),
                                  "pts": g.get("pts", 0), "final": mine, "opp_final": theirs}
    out = []
    for row in games.values():
        sides = row.pop("sides")
        teams = list(sides.items())
        if len(teams) == 1:   # opponent isn't in anyone's lineup
            name, s = teams[0]
            teams.append((s["opp"], {"pool": False, "home": not s["home"] and not row["neutral"], "owners": [],
                                     "final": s.get("opp_final"),
                                     "won": (not s["won"]) if s.get("won") is not None else None}))
        teams.sort(key=lambda kv: kv[1]["home"])           # away team first, home team second
        row["away"], row["home"] = ({"team": n, **s} for n, s in teams[:2])
        if row["start"] and not row["tbd"]:
            t = dt.datetime.fromisoformat(row["start"])
            row["time"] = t.strftime("%I:%M %p").lstrip("0")
        else:
            row["time"] = "TBD"
        out.append(row)
    out.sort(key=lambda r: (r["time"] == "TBD", r["start"]))
    label = dt.date.fromisoformat(today).strftime("%a, %b %d").replace(" 0", " ")
    return {"date": today, "label": label, "games": out}


def run(get_schedule=None, get_team_list=None, now=None, docs=DOCS, get_lines=None):
    get_schedule = get_schedule or (lambda tid: espn.schedule(tid, C.SEASON))
    get_team_list = get_team_list or espn.team_list
    get_lines = get_lines or espn.day_lines
    now = now or dt.datetime.now(ZoneInfo("America/New_York"))
    warnings = []

    teams = load_teams()
    if any(not t.get("espn_id") for t in teams):
        unresolved = resolve_espn_ids(teams, get_team_list())
        if unresolved and get_team_list is espn.team_list:
            try:
                unresolved = resolve_espn_ids(teams, espn.team_list(full=True))
            except RuntimeError as e:
                warnings.append(f"Full ESPN team list unavailable ({e})")
        save_teams(teams)
        if unresolved:
            warnings.append("Couldn't match these pool teams to ESPN (fill in espn_id in data/teams.csv): "
                            + ", ".join(unresolved))
    by_name = {t["team"]: t for t in teams}
    conf_of = {t["espn_id"]: t["conf"] for t in teams if t.get("espn_id")}
    d1_ids = set(conf_of)
    name_of = {t["espn_id"]: t["team"] for t in teams if t.get("espn_id")}

    entries, problems = load_entries(teams)
    warnings += problems
    seeds = load_seeds()

    picked = sorted({t for picks in entries.values() for t in picks})
    results = {}
    for name in picked:
        t = by_name[name]
        if not t.get("espn_id"):
            warnings.append(f"{name}: no ESPN id, scored as 0")
            continue
        try:
            games = get_schedule(t["espn_id"])
        except Exception as e:  # one bad fetch shouldn't kill the whole update
            warnings.append(f"{name}: couldn't fetch schedule ({e}); kept previous score")
            games = None
        if games is None:
            continue
        for g in games:   # league-list name for D-I opponents ("Loyola Marymount"), ESPN's short name otherwise
            g["opp_name"] = name_of.get(g["opp_id"]) or g.get("opp_short") or g["opp_name"]
        b = score_team(t, games, conf_of, d1_ids, seeds.get(name))
        warnings += b.pop("warnings")
        results[name] = b

    # keep yesterday's numbers for any team whose fetch failed
    prev = {}
    if (docs / "data.json").exists():
        prev = json.loads((docs / "data.json").read_text())
    for name in picked:
        if name not in results and name in prev.get("teams", {}):
            results[name] = prev["teams"][name]

    today = now.date().isoformat()
    totals = {e: sum(results.get(t, {}).get("total", 0) for t in picks) for e, picks in entries.items()}

    # history: one snapshot per day, used for "change since last update"
    history = [h for h in prev.get("history", []) if h["date"] != today]
    baseline = history[-1]["totals"] if history else {}
    # rank each entry held at the last daily snapshot (same tie rule: 1, 2, 3, 3, 5 ...)
    prev_rank = {e: 1 + sum(1 for x in baseline.values() if x > v) for e, v in baseline.items()}
    history.append({"date": today, "totals": totals})
    history = history[-200:]

    ranked = sorted(entries, key=lambda e: (-totals[e], e))
    standings = []
    for i, e in enumerate(ranked):
        rank = 1 + sum(1 for x in ranked if totals[x] > totals[e])
        standings.append({
            "rank": rank, "entry": e, "total": totals[e],
            "change": totals[e] - baseline[e] if e in baseline else None,
            "move": prev_rank[e] - rank if e in prev_rank else None,   # + = moved up, - = moved down
            "salary": sum(by_name[t]["salary"] for t in entries[e]),
            "teams": sorted(entries[e], key=lambda t: -results.get(t, {}).get("total", 0)),
        })

    owners = {}
    for e, picks in entries.items():
        for t in picks:
            owners.setdefault(t, []).append(e)

    data_today = todays_games(results, owners, today)
    data_yesterday = todays_games(results, owners, (now.date() - dt.timedelta(days=1)).isoformat())
    if data_today["games"]:
        try:
            lines = get_lines(today)
        except Exception:   # spreads are a nice-to-have; never fail the update over them
            lines = {}
        for g in data_today["games"]:
            g["line"] = lines.get(g["id"], "")

    data = {
        "updated": now.strftime("%Y-%m-%d %H:%M %Z"),
        "season": C.SEASON,
        "standings": standings,
        "teams": results,
        "team_info": {t: {"conf": by_name[t]["conf"], "salary": by_name[t]["salary"],
                          "owners": owners.get(t, [])} for t in picked},
        "history": history,
        "today": data_today,
        "yesterday": data_yesterday,
        "warnings": sorted(set(warnings)),
    }
    docs.mkdir(exist_ok=True)
    (docs / "data.json").write_text(json.dumps(data, indent=1))
    (docs / "index.html").write_text(render_html(data))
    return data


if __name__ == "__main__":
    d = run()
    print(f"Updated {d['updated']}: {len(d['standings'])} entries, {len(d['teams'])} teams")
    for s in d["standings"][:10]:
        print(f"  {s['rank']:>3}. {s['entry']:<25} {s['total']}")
    for w in d["warnings"]:
        print("  WARNING:", w, file=sys.stderr)
