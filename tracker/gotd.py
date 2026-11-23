"""Game of the Day: the game with the most at stake for the pool.

stakes = (entries involved + 3 x head-to-head pairs) x points the game is worth x closeness
Closeness slides smoothly with the spread: x1.5 at a pick'em down to x0.5 at 20 points.
A game against a non-Division I opponent has no line and is a near-certain blowout: x0.5.
Once the pick tips off it is locked for the day, so a later game's line move can't displace it.
"""
import datetime as dt
import re

from . import config as C
from .scoring import CONF_FINAL

NO_LINE = 99


def spread(g):
    m = re.search(r"-(\d+(?:\.\d+)?)", g.get("line") or "")
    return float(m.group(1)) if m else NO_LINE


def closeness(sp):
    return 1.0 if sp == NO_LINE else max(0.5, 1.5 - sp / 20)


def worth(g):
    k = g.get("kind")
    if k == "conf":
        return C.PTS_CONF_WIN
    if k == "nonconf":
        return C.PTS_NONCONF_WIN
    if k == "conf_tourney":
        return C.PTS_CONF_TOURNEY_WIN + (C.PTS_CONF_TOURNEY_CHAMP if CONF_FINAL.search(g.get("event") or "") else 0)
    if k == "ncaa":
        return C.PTS_NCAA_ROUND.get(g.get("round"), 2)
    return 1


def _owners(sd):
    return (sd.get("owners") or []) if sd.get("pool") else []


def stakes(g):
    a, h = _owners(g.get("away") or {}), _owners(g.get("home") or {})
    both = [e for e in a if e in h]
    n = len(set(a) | set(h))
    h2h = min(len(a) - len(both), len(h) - len(both))
    mismatch = any((g.get(k) or {}).get("d1") is False for k in ("away", "home"))
    return n, (n + 3 * h2h) * worth(g) * (0.5 if mismatch else closeness(spread(g)))


def started(g, now):
    if g.get("completed") or g.get("live"):
        return True
    try:
        return bool(g.get("start")) and dt.datetime.fromisoformat(g["start"].replace("Z", "+00:00")) <= now
    except ValueError:
        return False


def pick(today, prev=None, now=None):
    """Return {"date", "id"} for today's Game of the Day, or None. prev is the last stored pick."""
    today = today or {}
    games = today.get("games") or []
    now = now or dt.datetime.now(dt.timezone.utc)
    if prev and prev.get("date") == today.get("date"):
        locked = next((g for g in games if g.get("id") == prev.get("id")), None)
        if locked and started(locked, now):
            return prev
    scored = []
    for g in games:
        n, s = stakes(g)
        if n >= 2:
            scored.append((-s, spread(g), g.get("start") or "", g))
    if not scored:
        return None
    best = min(scored, key=lambda x: x[:3])[3]
    return {"date": today.get("date"), "id": best.get("id")}
