"""Thin client for ESPN's public (unofficial) college basketball JSON endpoints."""
import json, time, urllib.request, urllib.error

from .config import ESPN_BASE

UA = {"User-Agent": "Mozilla/5.0 (pool-tracker)"}


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


def team_list():
    """All Division I teams ESPN knows about: list of dicts with id + name variants."""
    data = fetch_json(f"{ESPN_BASE}/teams?groups=50&limit=1000")
    out = []
    for lg in data.get("sports", [{}])[0].get("leagues", []):
        for t in lg.get("teams", []):
            t = t.get("team", t)
            out.append({k: t.get(k, "") for k in
                        ("id", "location", "displayName", "shortDisplayName", "nickname", "abbreviation", "name")})
    return out


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
    return {
        "id": str(ev.get("id")),
        "date": ev.get("date", "")[:10],
        "season_type": int(st or season_type),
        "completed": completed,
        "won": bool(won) if completed else None,
        "opp_id": str(opp.get("id") or opp.get("team", {}).get("id")),
        "opp_name": opp.get("team", {}).get("displayName") or opp.get("team", {}).get("location", "?"),
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
    return sorted(games.values(), key=lambda g: g["date"])
