"""Keeps the site current from inside one long GitHub Actions job, instead of relying on GitHub's cron.

GitHub's scheduled runs are best-effort and often skipped, so the schedule only has to start this watcher once;
after that it keeps itself going:
  * from 5:45 AM Eastern it runs the morning full update (once per pool day),
  * while a game is in progress it refreshes scores every 10 minutes,
  * otherwise it sleeps until the next tip-off or the next morning update,
  * just before GitHub's 6-hour job limit it starts its own successor (workflow_dispatch) and exits.
Each update is committed and pushed only when the page actually changed.

Run:  python -m tracker.watch [--minutes 345]
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
DATA = "docs/data.json"
LIVE_EVERY = dt.timedelta(minutes=10)     # refresh cadence while games are on
IDLE_MAX = dt.timedelta(minutes=60)       # never sleep longer than this without re-checking
MORNING = dt.time(5, 45)                  # earliest morning full update (Eastern)


def sh(*cmd, check=True):
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check, text=True, capture_output=False)


def pull():
    sh("git", "fetch", "-q", "origin", "main")
    sh("git", "reset", "-q", "--hard", "origin/main")   # this job never holds local work between steps


def publish(message):
    sh("git", "add", "docs", "data/teams.csv")
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print("No changes", flush=True)
        return True
    sh("git", "commit", "-q", "-m", message)
    if subprocess.run(["git", "push", "-q", "origin", "HEAD:main"]).returncode != 0:
        # someone else pushed meanwhile (a code change, say): drop this commit; the next round redoes it on top
        print("Push rejected; will redo next round", flush=True)
        pull()
        return False
    return True


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def parse(ts):
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def plan(data, now):
    """What to do now, and when to look again: ('full'|'scores'|None, wake_at)."""
    now_et = now.astimezone(ET)
    pool_day = (now_et - dt.timedelta(hours=5)).date()
    next_morning = dt.datetime.combine(pool_day + dt.timedelta(days=1), MORNING, ET)
    have = (data.get("today") or {}).get("date")
    if have != pool_day.isoformat():
        if now_et.time() >= MORNING or now_et.date() != pool_day:
            return "full", now + dt.timedelta(minutes=1)
        return None, dt.datetime.combine(now_et.date(), MORNING, ET)
    games = [g for g in (data["today"].get("games") or []) if not g.get("completed")]
    starts = [s for s in (parse(g.get("start")) for g in games) if s]
    if any(s <= now for s in starts):
        return "scores", now + LIVE_EVERY
    later = [s for s in starts if s > now]
    wake = min(later) + dt.timedelta(minutes=3) if later else next_morning
    return None, min(wake, now + IDLE_MAX)


def main():
    budget = dt.timedelta(minutes=int(sys.argv[sys.argv.index("--minutes") + 1]) if "--minutes" in sys.argv else 345)
    stop = dt.datetime.now(dt.timezone.utc) + budget
    while True:
        now = dt.datetime.now(dt.timezone.utc)
        if now >= stop:
            break
        pull()
        action, wake = plan(load(), now)
        if action:
            cmd = [sys.executable, "-m", "tracker.run"] + (["--scores"] if action == "scores" else [])
            msg = f"Update standings {now.astimezone(ET):%Y-%m-%d}" if action == "full" else f"Update scores {now:%Y-%m-%d %H:%M} UTC"
            ok = subprocess.run(cmd).returncode == 0 and publish(msg)
            # after a failure (ESPN hiccup, rejected push) try again in a few minutes rather than waiting a full cycle
            wake = plan(load(), dt.datetime.now(dt.timezone.utc))[1] if ok else dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=3)
        pause = (min(wake, stop) - dt.datetime.now(dt.timezone.utc)).total_seconds()
        print(f"Next check {min(wake, stop).astimezone(ET):%a %I:%M %p} ET", flush=True)
        if pause > 0:
            time.sleep(pause)
    # hand off to a fresh job before GitHub's 6-hour limit
    if os.environ.get("GITHUB_ACTIONS"):
        sh("gh", "workflow", "run", "watch.yml", "--ref", "main", check=False)


if __name__ == "__main__":
    main()
