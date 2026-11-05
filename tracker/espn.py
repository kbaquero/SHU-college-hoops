"""Thin client for ESPN's public (unofficial) college basketball JSON endpoints."""
import json, time, urllib.request, urllib.error
import datetime as dt
from zoneinfo import ZoneInfo

from .config import ESPN_BASE

UA = {"User-Agent": "Mozilla/5.0 (pool-tracker)"}
ET = ZoneInfo("America/New_York")


def _when(iso):
    """ESPN gives UTC times; the pool lives on Eastern time (a 9 PM ET tip is already 'tomorrow' in UTC)."""
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ET)
        return t.date().isoformat(), t.isoformat()
    except (ValueError, AttributeError):
        return (iso or "")[:10], ""


def _tv(comp):
    names = []
    for b in comp.get("broadcasts") or []:
        n = (b.get("media") or {}).get("shortName") or ", ".join(b.get("names") or [])
        if n and n not in names:
            names.append(n)
    return ", ".join(names)


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == retries - 1:
                raise RuntimeError(f"ESPN request failed: {url}: {e}") from e
            time.sleep(2 * (attempt + 1))


def _teams(url):
    data = fetch_json(url)
    out = []
    for lg in data.get("sports", [{}])[0].get("leagues", []):
        for t in lg.get("teams", []):
            t = t.get("team", t)
            out.append({k: t.get(k, "") for k in
                        ("id", "location", "displayName", "shortDisplayName", "nickname", "abbreviation", "name")})
    return out


def team_list(full=False):
    """Teams ESPN knows about. Default: its Division I group. full=True: every team, which also
    catches schools still transitioning to Division I that ESPN leaves out of that group."""
    return _teams(f"{ESPN_BASE}/teams?limit=2000" if full else f"{ESPN_BASE}/teams?groups=50&limit=1000")


def _score(c):
    s = c.get("score")
    if isinstance(s, dict):
        s = s.get("displayValue", s.get("value"))
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None


def parse_event(ev, team_id, season_type):
    """Normalise one ESPN schedule event from `team_id`'s point of view."""
    comp = (ev.get("competitions") or [{}])[0]
    status = comp.get("status") or ev.get("status") or {}
    completed = bool(status.get("type", {}).get("completed"))
    me = opp = None
    for c in comp.get("competitors", []):
        cid = str(c.get("id") or c.get("team", {}).get("id"))
        if cid == str(team_id):
            me = c
        else:
            opp = c
    if me is None or opp is None:
        return None
    notes = " | ".join(n.get("headline", "") for n in comp.get("notes", []) if n.get("headline"))
    st = ev.get("seasonType", {})
    st = st.get("type", st.get("id")) if isinstance(st, dict) else st
    seed = me.get("seed")  # present on NCAA tournament games; curatedRank is the AP poll, so not used
    my_score, opp_score = _score(me), _score(opp)
    won = me.get("winner")
    if won is None and completed and my_score is not None and opp_score is not None:
        won = my_score > opp_score
    day, start = _when(ev.get("date", ""))
    return {
        "id": str(ev.get("id")),
        "date": day,
        "start": start,
        "time_tbd": ev.get("timeValid") is False or "TBD" in str(status.get("type", {}).get("detail", "")),
        "home": me.get("homeAway") == "home",
        "neutral": bool(comp.get("neutralSite")),
        "tv": _tv(comp),
        "season_type": int(st or season_type),
        "completed": completed,
        "won": bool(won) if completed else None,
        "opp_id": str(opp.get("id") or opp.get("team", {}).get("id")),
        "opp_name": opp.get("team", {}).get("displayName") or opp.get("team", {}).get("location", "?"),
        "opp_short": opp.get("team", {}).get("location") or opp.get("team", {}).get("shortDisplayName") or "",
        "score": f"{my_score}-{opp_score}" if completed else "",
        "headline": notes,
        "conf_flag": comp.get("conferenceCompetition"),
        "seed": seed,
    }


def schedule(team_id, season):
    """Regular season (type 2) + postseason (type 3) games for one team."""
    games = {}
    for stype in (2, 3):
        url = f"{ESPN_BASE}/teams/{team_id}/schedule?season={season}&seasontype={stype}"
        data = fetch_json(url)
        for ev in data.get("events", []):
            g = parse_event(ev, team_id, stype)
            if g:
                games[g["id"]] = g
        time.sleep(0.3)
    return sorted(games.values(), key=lambda g: (g["date"], g.get("start", "")))


def _line(odds):
    """Best-effort spread text from an ESPN odds entry, e.g. 'DUKE -7.5'."""
    if not odds:
        return ""
    o = odds[0] if isinstance(odds, list) else odds
    d = (o.get("details") or "").strip()
    if d and d.lower() not in ("off", "n/a"):
        return "Even" if d.upper() == "EVEN" else d
    sp = o.get("spread")
    return f"Spread {sp:+g}" if isinstance(sp, (int, float)) else ""


def _record(c):
    """Overall W-L from a scoreboard competitor, e.g. '3-1'."""
    recs = c.get("records") or c.get("record") or []
    if isinstance(recs, dict):
        recs = [recs]
    for want in ("total", "overall", None):
        for r in recs:
            if want is None or r.get("type") == want or r.get("name") == want:
                v = r.get("summary") or r.get("displayValue")
                if v:
                    return v
    return ""


def day_board(day):
    """{event_id: {"line": spread text, "records": {team_id: 'W-L'}}} for Division I games on `day`."""
    data = fetch_json(f"{ESPN_BASE}/scoreboard?dates={day.replace('-', '')}&groups=50&limit=500")
    out = {}
    for ev in data.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        recs, scores, winners = {}, {}, {}
        for c in comp.get("competitors", []):
            tid = str(c.get("id") or c.get("team", {}).get("id"))
            r = _record(c)
            if r:
                recs[tid] = r
            sc = _score(c)
            if sc is not None:
                scores[tid] = sc
            if c.get("winner") is not None:
                winners[tid] = bool(c.get("winner"))
        stype = (comp.get("status") or ev.get("status") or {}).get("type", {})
        out[str(ev.get("id"))] = {
            "line": _line(comp.get("odds")), "records": recs, "scores": scores, "winners": winners,
            "state": stype.get("state", ""),            # pre / in / post
            "completed": bool(stype.get("completed")),
            "headline": " | ".join(n.get("headline", "") for n in comp.get("notes", []) if n.get("headline")),
        }
    return out
