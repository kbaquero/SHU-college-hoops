"""Offline tests: fake ESPN data run through the full pipeline."""
import json, shutil, sys, tempfile, unittest, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tracker import config as C, teams as TM
from tracker.scoring import classify, score_team, ncaa_round
from tracker.espn import parse_event

TEAM = {"team": "Duke", "conf": "ACC", "salary": 18}
CONF_OF = {"150": "ACC", "153": "ACC", "2": "SEC", "99": "ACC"}
D1 = set(CONF_OF)


def g(gid, date, won, opp, stype=2, headline="", conf_flag=None, seed=None):
    return {"id": gid, "date": date, "season_type": stype, "completed": True, "won": won,
            "opp_id": opp, "opp_name": opp, "score": "70-60", "headline": headline,
            "conf_flag": conf_flag, "seed": seed}


class Scoring(unittest.TestCase):
    def test_regular_season(self):
        games = [g("1", "2026-11-05", True, "2"),                       # non-conf win  +1
                 g("2", "2026-11-09", False, "2"),                      # non-conf loss
                 g("3", "2027-01-05", True, "153"),                     # conf win (same conf) +2
                 g("4", "2027-01-08", False, "153"),                    # conf loss
                 g("5", "2026-11-20", True, "999"),                     # non-D1 win +1 (setting on)
                 g("6", "2026-11-25", True, "153", conf_flag=False)]   # conf mates, non-conf game +1
        b = score_team(TEAM, games, CONF_OF, D1)
        self.assertEqual((b["nonconf_w"], b["nonconf_l"], b["conf_w"], b["conf_l"]), (3, 1, 1, 1))
        self.assertEqual(b["total"], 1 + 2 + 1 + 1)

    def test_non_d1_switch(self):
        C.COUNT_NON_D1_WINS = False
        try:
            b = score_team(TEAM, [g("5", "2026-11-20", True, "999")], CONF_OF, D1)
            self.assertEqual(b["total"], 0)
        finally:
            C.COUNT_NON_D1_WINS = True

    def test_conf_tourney_champion_and_ncaa_run(self):
        games = [g("10", "2027-03-12", True, "153", 3, "ACC Tournament - Quarterfinal"),   # +2
                 g("11", "2027-03-13", True, "99", 3, "ACC Tournament - Semifinal"),       # +2
                 g("12", "2027-03-14", True, "153", 3, "ACC Tournament - Final"),          # +2 +5
                 g("20", "2027-03-20", True, "2", 3, "Men's Basketball Championship - East Region - 1st Round", seed="1"),  # +2
                 g("21", "2027-03-22", True, "2", 3, "Men's Basketball Championship - East Region - 2nd Round"),  # +4
                 g("22", "2027-03-27", True, "2", 3, "Men's Basketball Championship - East Region - Sweet 16"),  # +6
                 g("23", "2027-03-29", True, "2", 3, "Men's Basketball Championship - East Region - Elite 8"),   # +8
                 g("24", "2027-04-04", True, "2", 3, "Men's Basketball Championship - Final Four"),              # +10
                 g("25", "2027-04-06", True, "2", 3, "Men's Basketball Championship - National Championship")]  # +12
        b = score_team(TEAM, games, CONF_OF, D1)
        self.assertTrue(b["ct_champ"])
        self.assertEqual(b["pts_ct"], 6 + 5)
        self.assertEqual(b["seed"], 1)
        self.assertEqual(b["pts_ncaa"], 8 + 2 + 4 + 6 + 8 + 10 + 12)

    def test_semifinal_loss_not_champ(self):
        games = [g("10", "2027-03-12", True, "153", 3, "ACC Tournament - Quarterfinal"),
                 g("11", "2027-03-13", False, "99", 3, "ACC Tournament - Semifinal")]
        b = score_team(TEAM, games, CONF_OF, D1)
        self.assertFalse(b["ct_champ"])
        self.assertEqual(b["pts_ct"], 2)

    def test_semifinal_win_alone_not_champ(self):
        b = score_team(TEAM, [g("11", "2027-03-13", True, "99", 3, "ACC Tournament - Semifinals")], CONF_OF, D1)
        self.assertFalse(b["ct_champ"])

    def test_playin_counts_and_manual_seed(self):
        games = [g("30", "2027-03-17", True, "2", 3, "Men's Basketball Championship - First Four"),
                 g("31", "2027-03-19", False, "2", 3, "Men's Basketball Championship - South Region - 1st Round")]
        b = score_team(TEAM, games, CONF_OF, D1, manual_seed=16)
        self.assertEqual(b["pts_ncaa"], 2 + 2)   # 16-seed (2) + play-in win (2)
        self.assertTrue(b["ncaa_out"])

    def test_nit_and_in_season_tourneys_score_as_expected(self):
        nit = g("40", "2027-03-18", True, "2", 3, "NIT - First Round")
        maui = g("41", "2026-11-24", True, "2", 2, "Maui Invitational - Semifinal")
        self.assertEqual(classify(nit, "ACC", CONF_OF), "other_post")
        self.assertEqual(classify(maui, "ACC", CONF_OF), "nonconf")
        self.assertEqual(score_team(TEAM, [nit, maui], CONF_OF, D1)["total"], 1)

    def test_unknown_round_warns(self):
        b = score_team(TEAM, [g("50", "2027-03-20", True, "2", 3, "Men's Basketball Championship - Mystery Round", seed=3)], CONF_OF, D1)
        self.assertTrue(b["warnings"])
        self.assertEqual(b["pts_ncaa"], 6)

    def test_round_names(self):
        self.assertEqual(ncaa_round("Men's Basketball Championship - West Region - Sweet 16"), "s16")
        self.assertEqual(ncaa_round("Men's Basketball Championship - Final Four"), "f4")
        self.assertEqual(ncaa_round("Men's Basketball Championship - Opening Round"), "playin")


class Parsing(unittest.TestCase):
    def test_parse_espn_schedule_event(self):
        ev = {"id": "401", "date": "2026-11-04T00:00Z", "seasonType": {"type": 2},
              "competitions": [{"conferenceCompetition": False, "status": {"type": {"completed": True}},
                                "notes": [{"headline": "Champions Classic"}],
                                "competitors": [
                                    {"id": "150", "winner": True, "score": {"value": 81.0, "displayValue": "81"}, "team": {"id": "150", "displayName": "Duke Blue Devils"}},
                                    {"id": "2", "winner": False, "score": {"value": 70.0, "displayValue": "70"}, "team": {"id": "2", "displayName": "Auburn Tigers"}}]}]}
        p = parse_event(ev, "150", 2)
        self.assertEqual((p["won"], p["opp_id"], p["score"], p["conf_flag"]), (True, "2", "81-70", False))

    def test_unplayed_game(self):
        ev = {"id": "402", "date": "2027-01-01T00:00Z",
              "competitions": [{"status": {"type": {"completed": False}},
                                "competitors": [{"id": "150", "team": {"id": "150"}}, {"id": "2", "team": {"id": "2"}}]}]}
        p = parse_event(ev, "150", 2)
        self.assertFalse(p["completed"])
        self.assertIsNone(p["won"])


class TodaysGames(unittest.TestCase):
    def test_late_tip_is_eastern_date_and_time(self):
        ev = {"id": "500", "date": "2026-11-05T02:00Z", "timeValid": True,
              "competitions": [{"neutralSite": False, "status": {"type": {"completed": False, "detail": "Wed, November 4th at 9:00 PM EST"}},
                                "broadcasts": [{"media": {"shortName": "ESPN2"}}],
                                "competitors": [{"id": "150", "homeAway": "home", "team": {"id": "150", "displayName": "Duke Blue Devils"}},
                                                {"id": "2", "homeAway": "away", "team": {"id": "2", "displayName": "Auburn Tigers"}}]}]}
        p = parse_event(ev, "150", 2)
        self.assertEqual((p["date"], p["home"], p["tv"], p["time_tbd"]), ("2026-11-04", True, "ESPN2", False))

    def test_both_pool_teams_one_row_and_lone_team_row(self):
        from tracker.run import todays_games
        mk = lambda gid, start, home, opp, tbd=False: {"id": gid, "date": "2026-11-04", "start": start, "time_tbd": tbd,
                                                      "home": home, "neutral": False, "tv": "", "completed": False,
                                                      "won": None, "score": "", "opp_name": opp, "kind": "nonconf"}
        results = {"Duke": {"games": [mk("1", "2026-11-04T21:00:00-05:00", True, "Florida Gators")]},
                   "Florida": {"games": [mk("1", "2026-11-04T21:00:00-05:00", False, "Duke Blue Devils")]},
                   "Navy": {"games": [mk("2", "2026-11-04T19:00:00-05:00", False, "Army Black Knights"),
                                      {**mk("3", "2026-11-05T19:00:00-05:00", True, "x"), "date": "2026-11-05"}]},
                   "Siena": {"games": [mk("4", "", True, "Marist Red Foxes", tbd=True)]}}
        owners = {"Duke": ["Kevin B.", "Joe H."], "Florida": ["Kevin B."], "Navy": ["Kevin B."], "Siena": ["Kevin B."]}
        t = todays_games(results, owners, "2026-11-04")
        self.assertEqual(t["label"], "Wed, Nov 4")
        self.assertEqual([g["id"] for g in t["games"]], ["2", "1", "4"])       # by tip time, TBD last
        navy, big, siena = t["games"]
        self.assertEqual((navy["time"], navy["away"]["team"], navy["home"]["team"], navy["home"]["pool"]),
                         ("7:00 PM", "Navy", "Army Black Knights", False))
        self.assertEqual((big["away"]["team"], big["home"]["team"], big["home"]["owners"]), ("Florida", "Duke", ["Kevin B.", "Joe H."]))
        self.assertEqual(siena["time"], "TBD")

    def test_spread_text(self):
        from tracker.espn import _line
        self.assertEqual(_line([{"details": "DUKE -7.5", "overUnder": 151.5}]), "DUKE -7.5")
        self.assertEqual(_line([{"details": "EVEN"}]), "Even")
        self.assertEqual(_line([{"details": "OFF"}]), "")
        self.assertEqual(_line([{"spread": -3.0}]), "Spread -3")
        self.assertEqual(_line(None), "")

    def test_overall_record_counts_every_game(self):
        games = [g("1", "2026-11-05", True, "2"), g("2", "2027-01-05", False, "153"),
                 g("3", "2027-03-20", True, "2", 3, "Men's Basketball Championship - 1st Round", seed="4"),
                 g("4", "2027-03-22", False, "2", 3, "Men's Basketball Championship - 2nd Round")]
        b = score_team(TEAM, games, CONF_OF, D1)
        self.assertEqual((b["w"], b["l"]), (2, 2))


class Resolution(unittest.TestCase):
    def test_name_matching(self):
        rows = [{"team": n, "espn_id": ""} for n in
                ["Kansas St.", "St. John's", "Miami FL", "Miami OH", "SIUE", "Connecticut", "Southern", "Texas A&M"]]
        espn = [{"id": "1", "location": "Kansas State", "displayName": "Kansas State Wildcats"},
                {"id": "2", "location": "St. John's", "displayName": "St. John's Red Storm"},
                {"id": "3", "location": "Miami", "displayName": "Miami Hurricanes"},
                {"id": "4", "location": "Miami (OH)", "displayName": "Miami (OH) RedHawks"},
                {"id": "5", "location": "SIU Edwardsville", "displayName": "SIU Edwardsville Cougars"},
                {"id": "6", "location": "UConn", "displayName": "UConn Huskies"},
                {"id": "7", "location": "Southern", "displayName": "Southern Jaguars"},
                {"id": "8", "location": "Southern Miss", "displayName": "Southern Miss Golden Eagles"},
                {"id": "9", "location": "Texas A&M", "displayName": "Texas A&M Aggies"},
                {"id": "10", "location": "Texas A&M-Corpus Christi", "displayName": "Texas A&M-Corpus Christi Islanders"}]
        self.assertEqual(TM.resolve_espn_ids(rows, espn), [])
        self.assertEqual([r["espn_id"] for r in rows], ["1", "2", "3", "4", "5", "6", "7", "9"])


class Pipeline(unittest.TestCase):
    def test_full_run_offline(self):
        from tracker import run as R
        tmp = Path(tempfile.mkdtemp())
        data_bak = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "data", data_bak, dirs_exist_ok=True)
        try:
            # give every pool team a fake ESPN id so no network is needed
            rows = TM.load_teams()
            for i, r in enumerate(rows):
                r["espn_id"], r["espn_name"] = str(1000 + i), r["team"]
            TM.save_teams(rows)
            # the test uses its own single entry so it doesn't depend on the real league file
            picks = ["Duke", "Michigan", "Kansas St.", "St. John's", "Florida",
                     "Howard", "Navy", "Siena", "Mercyhurst", "SIUE"]
            (ROOT / "data" / "entries.csv").write_text("entry,team\n" + "".join(f"Kevin,{t}\n" for t in picks))
            ids = {r["team"]: r["espn_id"] for r in rows}
            duke = ids["Duke"]

            def sched(tid):
                return [g("a" + tid, "2026-11-05", True, "999"),
                        g("b" + tid, "2027-01-10", tid == duke, ids["Virginia"] if tid == duke else "999")]
            d = R.run(get_schedule=sched, get_team_list=lambda: [], get_lines=lambda d: {},
                      now=dt.datetime(2026, 11, 10, 6, 0), docs=tmp)
            self.assertEqual(d["standings"][0]["entry"], "Kevin")
            self.assertEqual(d["teams"]["Duke"]["total"], 1 + 2)
            vgames = [x for x in d["teams"]["Duke"]["games"] if x["opp_id"] == ids["Virginia"]]
            self.assertEqual(vgames[0]["opp_name"], "Virginia")   # league-list name, not ESPN's long name
            self.assertEqual(d["standings"][0]["total"], 10 * 1 + 2)
            html = (tmp / "index.html").read_text()
            self.assertIn("SHU College Hoops Pool", html)
            self.assertIn('rel="manifest"', html)
            # second day: change since last update is computed
            d2 = R.run(get_schedule=sched, get_team_list=lambda: [], get_lines=lambda d: {},
                       now=dt.datetime(2026, 11, 11, 6, 0), docs=tmp)
            self.assertEqual(d2["standings"][0]["change"], 0)
            self.assertEqual(len(d2["history"]), 2)
        finally:
            shutil.copytree(data_bak, ROOT / "data", dirs_exist_ok=True)
            shutil.rmtree(tmp); shutil.rmtree(data_bak)


if __name__ == "__main__":
    unittest.main()
