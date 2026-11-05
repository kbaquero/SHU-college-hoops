"""Daily update: pull results, score every entry, write docs/data.json + docs/index.html.

Usage:  python -m tracker.run            (normal run against ESPN)
"""
import json, re, sys, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from . import config as C, espn
from .teams import load_teams, save_teams, resolve_espn_ids, load_entries, load_seeds, load_full_names
from .scoring import score_team, game_points, ncaa_round
from .render import render_html

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def event_label(headline, kind=""):
    """Short event name for the game lists, from ESPN's game note:
    'Big East Tournament - Quarterfinal' -> 'Big East Tournament · Quarterfinal'
    'Men's Basketball Championship - East Region - Sweet 16' -> 'East Region' (the round is already on the tag)."""
    parts = [p.strip() for p in (headline or "").split(" | ")[0].split(" - ") if p.strip()]
    if not parts:
        return ""
    if kind == "ncaa":
        parts = [p for p in parts if not re.search(r"men's basketball championship|ncaa", p, re.I)
                 and ncaa_round(p) is None]
    return " · ".join(parts)


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
                "kind": g.get("kind", ""), "round": g.get("round"),
                "final_label": espn.final_label(g.get("status_detail", "")),
                "event": event_label(g.get("headline", ""), g.get("kind", "")), "sides": {}})
            mine, theirs = _pts_pair(g.get("score", ""))
            row["sides"][team] = {"pool": True, "home": bool(g.get("home")), "owners": owners.get(team, []),
                                  "won": g.get("won"), "score": g.get("score", ""), "opp": g.get("opp_name", ""),
                                  "pts": g.get("pts", 0), "final": mine, "opp_final": theirs,
                                  "opp_id": g.get("opp_id", "")}
    out = []
    for row in games.values():
        sides = row.pop("sides")
        teams = list(sides.items())
        if len(teams) == 1:   # opponent isn't in anyone's lineup
            name, s = teams[0]
            teams.append((s["opp"], {"pool": False, "home": not s["home"] and not row["neutral"], "owners": [],
                                     "id": s.get("opp_id", ""),
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


def rebuild_history(results, entries, today):
    """Morning snapshots for every day from the first game until yesterday. A snapshot dated D counts
    points from games played before D, matching what the morning update on D would have shown.
    (Seed points aren't tied to a game, so this is only exact before Selection Sunday.)"""
    dated = [(g["date"], g.get("pts", 0), t) for t, b in results.items() for g in b.get("games", [])
             if g.get("completed") and g.get("date")]
    if not dated:
        return []
    first = min(d for d, _, _ in dated)
    day, end, out = dt.date.fromisoformat(first), dt.date.fromisoformat(today), []
    while day < end:
        d = day.isoformat()
        team_pts = {}
        for gd, pts, t in dated:
            if gd < d:
                team_pts[t] = team_pts.get(t, 0) + pts
        out.append({"date": d, "totals": {e: sum(team_pts.get(t, 0) for t in picks) for e, picks in entries.items()},
                    "rebuilt": True})
        day += dt.timedelta(days=1)
    return out


def run(get_schedule=None, get_team_list=None, now=None, docs=DOCS, get_lines=None):
    get_schedule = get_schedule or (lambda tid: espn.schedule(tid, C.SEASON))
    get_team_list = get_team_list or espn.team_list
    get_lines = get_lines or espn.day_board
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
    # The pool's day rolls over at 5 AM Eastern, not midnight: runs between midnight and 5 AM still belong to
    # the previous evening, so late games finish in Today's games and the standings only move each morning.
    pool_day = (now - dt.timedelta(hours=5)).date()
    today = pool_day.isoformat()
    todays = {}
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
        # Standings count only games before today (Eastern), so a full run at any hour matches the morning
        # numbers; today's games are shown separately and become official in tomorrow morning's update.
        b = score_team(t, [g for g in games if g["date"] < today], conf_of, d1_ids, seeds.get(name))
        warnings += b.pop("warnings")
        results[name] = b
        live = score_team(t, games, conf_of, d1_ids, seeds.get(name))
        todays[name] = {"games": [g for g in live["games"] if g["date"] == today]}

    # keep yesterday's numbers for any team whose fetch failed
    prev = {}
    if (docs / "data.json").exists():
        prev = json.loads((docs / "data.json").read_text())
    for name in picked:
        if name not in results and name in prev.get("teams", {}):
            results[name] = prev["teams"][name]

    totals = {e: sum(results.get(t, {}).get("total", 0) for t in picks) for e, picks in entries.items()}

    # history: one snapshot per day, used for "change since last update"
    history = [h for h in prev.get("history", []) if h["date"] != today]
    if not history:   # no earlier snapshots (first run, or lost history): rebuild them from the game logs
        history = rebuild_history(results, entries, today)
    baseline = history[-1]["totals"] if history else {}
    # rank each entry held at the last daily snapshot (same tie rule: 1, 2, 3, 3, 5 ...)
    prev_rank = {e: 1 + sum(1 for x in baseline.values() if x > v) for e, v in baseline.items()}
    history.append({"date": today, "totals": totals})
    history = history[-200:]

    full_names = load_full_names()
    ranked = sorted(entries, key=lambda e: (-totals[e], e))
    standings = []
    for i, e in enumerate(ranked):
        rank = 1 + sum(1 for x in ranked if totals[x] > totals[e])
        standings.append({
            "rank": rank, "entry": e, "full": full_names.get(e, e), "total": totals[e],
            "change": totals[e] - baseline[e] if e in baseline else None,
            "move": prev_rank[e] - rank if e in prev_rank else None,   # + = moved up, - = moved down
            "salary": sum(by_name[t]["salary"] for t in entries[e]),
            "teams": sorted(entries[e], key=lambda t: -results.get(t, {}).get("total", 0)),
        })

    owners = {}
    for e, picks in entries.items():
        for t in picks:
            owners.setdefault(t, []).append(e)

    data_today = todays_games(todays, owners, today)
    data_yesterday = todays_games(results, owners, (pool_day - dt.timedelta(days=1)).isoformat())
    # spreads (today) and opponents' records (both days) come from ESPN's daily scoreboard
    # spreads already captured by earlier runs (morning or evening); kept once ESPN drops a line at tip-off
    saved_lines = {g["id"]: g["line"] for blk in ("today", "yesterday")
                   for g in (prev.get(blk) or {}).get("games", []) if g.get("line")}
    for block in (data_today, data_yesterday):
        if not block["games"]:
            continue
        try:
            board = get_lines(block["date"])
        except Exception:   # nice-to-have; never fail the update over it
            board = {}
        for g in block["games"]:
            info = board.get(g["id"]) or {}
            if isinstance(info, str):   # tolerate a plain {event: spread} mapping
                info = {"line": info}
            g["line"] = (info.get("line") if block is data_today else "") or saved_lines.get(g["id"], "")
            for side in (g["away"], g["home"]):
                if side["pool"]:
                    b = results.get(side["team"], {})
                    side["record"] = f'{b.get("w", 0)}-{b.get("l", 0)}' if b else ""
                    if block is data_today and g["completed"]:   # standings records stop at this morning
                        side["record"] = _bump(side["record"], side.get("won"))
                else:
                    side["record"] = (info.get("records") or {}).get(side.get("id", ""), "")
        if block is data_today and isinstance(board, dict):
            apply_board(block["games"], {k: v for k, v in board.items() if isinstance(v, dict)}, now)   # schedules can lag; the scoreboard is fresher

    data = {
        "updated": now.strftime("%Y-%m-%d %H:%M %Z"),
        "through": (pool_day - dt.timedelta(days=1)).strftime("%a, %b %d").replace(" 0", " "),
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


def _bump(record, won):
    """'3-1' + a win -> '4-1'. Leaves unknown records alone."""
    try:
        w, l = (int(x) for x in record.split("-"))
    except (ValueError, AttributeError):
        return record
    return f"{w + 1}-{l}" if won else f"{w}-{l + 1}" if won is False else record


def _clock(detail):
    """ESPN's in-game status, tidied: '8:12 - 2nd Half' -> '8:12 2nd', 'Halftime' stays."""
    d = (detail or "").replace(" - ", " ").replace(" Half", "").replace("1st OT", "OT").strip()
    return "Halftime" if d.lower() in ("half", "halftime") else d or "In progress"


def apply_board(games, board, now):
    """Apply ESPN's live scoreboard to Today's games: newer pregame lines, in-progress snapshots,
    and finals (scores, points preview, records). Returns True if anything changed."""
    teams = load_teams()
    id_of = {t["team"]: t["espn_id"] for t in teams if t.get("espn_id")}
    d1 = set(id_of.values())
    changed = False
    for g in games:
        info = board.get(g["id"])
        if not info:
            continue
        if info.get("state") == "pre" and info.get("line") and info["line"] != g.get("line"):
            g["line"] = info["line"]          # newer pregame line; frozen once the game tips
            changed = True
        if not g.get("event") and info.get("headline"):
            g["event"] = event_label(info["headline"], g.get("kind", ""))
            changed = True
        if g.get("completed"):
            continue
        sides = (g["away"], g["home"])
        ids = [id_of.get(s["team"], "") if s["pool"] else s.get("id", "") for s in sides]
        scores, winners = info.get("scores", {}), info.get("winners", {})
        if info.get("state") == "in" and not info.get("completed"):
            # caught mid-game: keep a snapshot of the score and clock as of this update
            live = {"detail": _clock(info.get("detail", "")), "as_of": now.strftime("%-I:%M %p")}
            snap = [scores.get(i) for i in ids]
            if snap != [s.get("live") for s in sides] or live["detail"] != (g.get("live") or {}).get("detail"):
                for s, v in zip(sides, snap):
                    s["live"] = v
                g["live"] = live
                changed = True
            continue
        if not info.get("completed"):
            continue
        if g.get("kind") == "ncaa" and not g.get("round"):
            g["round"] = ncaa_round(info.get("headline", ""))
        g.pop("live", None)
        g["final_label"] = espn.final_label(info.get("detail", ""))
        for k, s in enumerate(sides):
            me, opp = ids[k], ids[1 - k]
            s.pop("live", None)
            s["final"] = scores.get(me)
            won = winners.get(me)
            if won is None and s["final"] is not None and scores.get(opp) is not None:
                won = s["final"] > scores[opp]
            s["won"] = won
            s["record"] = _bump(s.get("record", ""), won)
            if s["pool"]:
                s["pts"] = game_points(g.get("kind"), won, g.get("round"), info.get("headline", ""), opp in d1)
        g["completed"] = True
        changed = True
    return changed


def update_scores(get_board=None, now=None, docs=DOCS):
    """Evening update: refresh only Today's games (finals, scores, preview points, latest pregame spread).
    Standings and everything else keep their morning numbers."""
    get_board = get_board or espn.day_board
    now = now or dt.datetime.now(ZoneInfo("America/New_York"))
    path = docs / "data.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    td = data.get("today") or {}
    if not td.get("games"):
        return data
    board = get_board(td["date"])   # the morning's date, so 12-1 AM runs still finish off "today"
    changed = apply_board(td["games"], board, now)
    if changed:
        data["scores_updated"] = now.strftime("%-I:%M %p")
        path.write_text(json.dumps(data, indent=1))
        (docs / "index.html").write_text(render_html(data))
    return data


if __name__ == "__main__":
    if "--scores" in sys.argv:
        d = update_scores()
        print("Scores updated" if d and d.get("scores_updated") else "No score changes")
        sys.exit(0)
    d = run()
    print(f"Updated {d['updated']}: {len(d['standings'])} entries, {len(d['teams'])} teams")
    for s in d["standings"][:10]:
        print(f"  {s['rank']:>3}. {s['entry']:<25} {s['total']}")
    for w in d["warnings"]:
        print("  WARNING:", w, file=sys.stderr)
