# SHU College Hoops Pool

Scores every entry in the season-long pool and publishes a standings page. A GitHub
Action runs every morning (~5:47 AM Eastern), pulls results from ESPN, re-scores
everything, and commits the updated page.

## Setup (about 10 minutes)

1. **Create a repo** on GitHub (private is fine) and push this folder to it:
   ```bash
   cd pool-tracker
   git init && git add . && git commit -m "Pool tracker"
   git branch -M main
   git remote add origin https://github.com/<you>/pool-tracker.git
   git push -u origin main
   ```
2. **Allow the Action to push**: Settings → Actions → General → Workflow permissions →
   *Read and write permissions* → Save.
3. **Turn on the page**: Settings → Pages → Source: *Deploy from a branch* →
   Branch `main`, folder `/docs` → Save. Your standings will be at
   `https://<you>.github.io/pool-tracker/`.
   (GitHub Pages on a private repo needs a paid plan. On a free account, make the repo public;
   it only contains team picks.)
4. **Run it once**: Actions tab → *Update standings* → *Run workflow*. On the first run, it
   matches all 365 pool teams to ESPN team IDs and saves them in `data/teams.csv`.
   If any team can't be matched, it shows up in the **Needs attention** box on the page.
   Fill in that team's `espn_id` by hand (the number in the team's ESPN URL, e.g.
   `espn.com/mens-college-basketball/team/_/id/150/duke` → `150`).

## Installing it as an app

The page works as a home-screen app ("SHU Hoops" under the basketball icon). It opens
full-screen and shows the last standings even with no signal.

- **iPhone:** open the page in Safari → Share → **Add to Home Screen**.
- **Android:** open it in Chrome → ⋮ menu → **Add to Home screen** / **Install app**.

The app updates itself because it's the same page. To change the icon, replace the files in
`docs/icons/` (SVG source plus 180/192/512 px PNGs) and bump `CACHE` in `docs/sw.js`.

## Adding entries

Edit `data/entries.csv`, with one row per pick and team names spelled exactly as in the
salary list (`data/teams.csv`):

```
entry,team
Kevin,Duke
Kevin,Michigan
...
```

Pushing a change to `data/` re-scores immediately. Every entry is checked for 10 teams,
the 100 cap, and one team from each Power 5 conference. Problems show up on the page.

## March checklist

- **Seeds**: the script reads NCAA seeds from ESPN when it can. On Selection Sunday, open
  the page. Any picked team in the tournament without a seed is flagged. Add those
  teams to `data/seeds.csv` (`team,seed`). Manual seeds override ESPN's.
- **Round names**: rounds are recognised from ESPN's game labels ("1st Round",
  "Sweet 16", "First Four", ...). The 76-team field is new, so if ESPN uses a new label,
  the page flags it. Add the wording to `NCAA_ROUND_PATTERNS` in `tracker/config.py`.
  Play-in/opening-round wins score 2, the same as a Round of 64 win, per the footnote.

## Scoring rules (tracker/config.py)

| Category | Pts |
|---|---|
| Non-conference regular season win | 1 |
| Conference regular season win | 2 |
| Conference tournament win | 2 |
| Conference tournament championship | +5 |
| NCAA seed 1 / 2-4 / 5-8 / 9-16 | 8 / 6 / 4 / 2 |
| NCAA win: play-in or R64 / R32 / S16 / E8 / F4 / title game | 2 / 4 / 6 / 8 / 10 / 12 |

`COUNT_NON_D1_WINS` (default `True`) controls whether wins over non-Division I
opponents count. Flip it if the commissioner rules otherwise.

How games are classified:
- **Conference vs. non-conference**: ESPN's conference-game flag. Falls back to "both teams
  are in the same conference in the salary list".
- **Conference tournament**: postseason games against a conference opponent. The title is
  awarded when a team wins a game labelled Final/Championship, or wins out and then shows
  up in the NCAA tournament.
- **NIT / Crown / CBI games** score nothing.

## Notes

- Data comes from ESPN's public JSON endpoints, which are free and need no key but are
  undocumented. The pool's official source is ncaa.com, so use it to settle disputes.
- If a team's fetch fails one morning, that team keeps the previous day's score and is
  flagged. The next run catches up.
- Run locally: `python -m tracker.run` (Python 3.9+, no packages to install).
  Tests: `python -m unittest discover -s tests`.

## Update schedule

- **Morning (about 5:50 AM Eastern):** full update. Standings, Δ, rank arrows, chart and team logs count games
  through the previous day. The pool's day rolls over at 5 AM Eastern, so late games always land in the next
  morning's update.
- **Evenings (hourly, about 7 PM to 1 AM Eastern):** only Today's games changes: finals, in-progress snapshots,
  pregame spreads. Standings keep the morning numbers.
- **Any push to `data/`, `tracker/`, `tests/` or `.github/`** runs a full update, which is safe at any hour.

GitHub's own cron schedules (in the workflow) often fire late or get skipped, so two Claude scheduled tasks
("SHU pool – morning standings nudge" and "SHU pool – evening scores nudge") also push a timestamp to
`data/.tick` on that schedule to start the workflow. Either path produces the same result.
