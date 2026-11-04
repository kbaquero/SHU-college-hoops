"""Load the pool's team list and entries, and map pool team names to ESPN team IDs."""
import csv, difflib, re
from pathlib import Path

from .config import SALARY_CAP, POWER5, TEAMS_PER_ENTRY

DATA = Path(__file__).resolve().parent.parent / "data"

# Pool name -> ESPN name, where normalising the text isn't enough
ALIASES = {
    "Connecticut": "UConn", "Miami FL": "Miami", "Miami OH": "Miami (OH)", "N.C. State": "NC State",
    "Mississippi": "Ole Miss", "Illinois Chicago": "UIC", "Seattle": "Seattle U", "Penn": "Pennsylvania",
    "Queens": "Queens University", "St. Thomas": "St. Thomas-Minnesota", "Sam Houston St.": "Sam Houston",
    "Appalachian St.": "App State", "LSU New Orleans": "New Orleans", "Southeastern Louisiana": "SE Louisiana",
    "Southeast Missouri": "Southeast Missouri State", "SIUE": "SIU Edwardsville", "Tennessee Martin": "UT Martin",
    "Nebraska Omaha": "Omaha", "Albany": "UAlbany", "American": "American University",
    "LIU": "Long Island University", "Loyola MD": "Loyola Maryland", "USC Upstate": "South Carolina Upstate",
    "Gardner Webb": "Gardner-Webb", "Bethune Cookman": "Bethune-Cookman", "Grambling St.": "Grambling",
    "Arkansas Pine Bluff": "Arkansas-Pine Bluff", "Louisiana Monroe": "UL Monroe", "IU Indy": "IU Indianapolis",
    "FIU": "Florida International", "CSUN": "Cal State Northridge", "Cal Baptist": "California Baptist",
    "Texas A&M Corpus Chris": "Texas A&M-Corpus Christi", "Cal St. Fullerton": "Cal State Fullerton",
    "Cal St. Bakersfield": "Cal State Bakersfield", "Mississippi Valley St.": "Mississippi Valley State",
    "Saint Mary's": "Saint Mary's", "Hawaii": "Hawai'i",
}


def norm(s):
    s = s.lower().replace("&", "and").replace("'", "").replace("’", "")
    s = re.sub(r"\bstate\b", "st", s)
    s = re.sub(r"\bsaint\b", "st", s)
    return re.sub(r"[^a-z0-9]", "", s)


def load_teams():
    with open(DATA / "teams.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["salary"] = int(r["salary"])
    return rows


def save_teams(rows):
    cols = ["conf", "team", "kenpom", "salary", "espn_id", "espn_name"]
    with open(DATA / "teams.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def resolve_espn_ids(rows, espn_teams):
    """Fill in espn_id for any team that doesn't have one yet. Returns names it couldn't match."""
    index = {}
    for t in espn_teams:
        for k in ("location", "shortDisplayName", "displayName", "nickname"):
            if t.get(k):
                index.setdefault(norm(t[k]), set()).add(t["id"])
    by_id = {t["id"]: t for t in espn_teams}
    taken = {r["espn_id"] for r in rows if r.get("espn_id")}
    unresolved = []
    for r in rows:
        if r.get("espn_id"):
            continue
        key = norm(ALIASES.get(r["team"], r["team"]))
        ids = index.get(key, set()) - taken
        if len(ids) != 1:
            close = difflib.get_close_matches(key, index.keys(), n=2, cutoff=0.88)
            cands = set().union(*(index[c] for c in close)) - taken if close else set()
            ids = cands if len(cands) == 1 else set()
        if ids:
            tid = ids.pop()
            r["espn_id"], r["espn_name"] = tid, by_id[tid]["displayName"]
            taken.add(tid)
        else:
            unresolved.append(r["team"])
    return unresolved


def load_entries(teams):
    by_name = {t["team"]: t for t in teams}
    entries, problems = {}, []
    with open(DATA / "entries.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            name, team = r["entry"].strip(), r["team"].strip()
            if not name:
                continue
            if team not in by_name:
                hint = difflib.get_close_matches(team, by_name, n=1)
                problems.append(f"{name}: unknown team '{team}'" + (f" (did you mean '{hint[0]}'?)" if hint else ""))
                continue
            entries.setdefault(name, []).append(team)
    for name, picks in entries.items():
        sal = sum(by_name[t]["salary"] for t in picks)
        confs = {by_name[t]["conf"] for t in picks}
        if len(picks) != TEAMS_PER_ENTRY:
            problems.append(f"{name}: {len(picks)} teams (needs {TEAMS_PER_ENTRY})")
        if len(set(picks)) != len(picks):
            problems.append(f"{name}: duplicate team")
        if sal > SALARY_CAP:
            problems.append(f"{name}: salary {sal} is over the cap of {SALARY_CAP}")
        missing = [c for c in POWER5 if c not in confs]
        if missing:
            problems.append(f"{name}: no team from {', '.join(missing)}")
    return entries, problems


def load_seeds():
    p = DATA / "seeds.csv"
    seeds = {}
    if p.exists():
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("team") and r.get("seed"):
                    seeds[r["team"].strip()] = int(r["seed"])
    return seeds
