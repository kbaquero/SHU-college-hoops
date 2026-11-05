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
        self.assertEqual([x["round"] for x in b["games"] if x["kind"] == "ncaa"], ["r64", "r32", "s16", "e8", "f4", "final"])

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

    def test_final_scores_and_points_for_yesterday(self):
        from tracker.run import todays_games
        res = {"Navy": {"games": [{"id": "9", "date": "2026-11-03", "start": "2026-11-03T19:00:00-05:00", "time_tbd": False,
                                   "home": True, "neutral": False, "tv": "", "completed": True, "won": False,
                                   "score": "39-91", "opp_name": "George Washington", "kind": "nonconf", "pts": 0}]}}
        g = todays_games(res, {"Navy": ["Kevin B."]}, "2026-11-03")["games"][0]
        self.assertEqual((g["home"]["team"], g["home"]["final"], g["home"]["pts"], g["home"]["won"]), ("Navy", 39, 0, False))
        self.assertEqual((g["away"]["team"], g["away"]["final"], g["away"]["won"], g["away"]["pool"]), ("George Washington", 91, True, False))

    def test_rebuild_history_from_game_logs(self):
        from tracker.run import rebuild_history
        mk = lambda d, pts: {"date": d, "pts": pts, "completed": True}
        res = {"Duke": {"games": [mk("2026-11-02", 1), mk("2026-11-03", 1)]}, "Navy": {"games": [mk("2026-11-03", 2)]}}
        h = rebuild_history(res, {"Kevin": ["Duke", "Navy"], "Joe": ["Navy"]}, "2026-11-04")
        self.assertEqual([x["date"] for x in h], ["2026-11-02", "2026-11-03"])
        self.assertEqual([x["totals"] for x in h], [{"Kevin": 0, "Joe": 0}, {"Kevin": 1, "Joe": 0}])

    def test_scoreboard_record(self):
        from tracker.espn import _record
        self.assertEqual(_record({"records": [{"name": "overall", "type": "total", "summary": "3-1"},
                                              {"name": "Home", "type": "home", "summary": "2-0"}]}), "3-1")
        self.assertEqual(_record({"records": [{"type": "home", "summary": "2-0"}, {"type": "total", "summary": "4-2"}]}), "4-2")
        self.assertEqual(_record({}), "")

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
                        g("b" + tid, "2026-11-08", tid == duke, ids["Virginia"] if tid == duke else "999")]
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
            self.assertEqual(d2["standings"][0]["move"], 0)
            self.assertEqual(d["standings"][0]["move"], 0)        # first run rebuilds earlier days from game logs
            self.assertEqual(d["history"][0]["date"], "2026-11-05")       # first game day
            self.assertEqual(d["history"][-2]["totals"]["Kevin"], 12)    # rebuilt Nov 9 snapshot: Nov 5 wins + Duke's Nov 8 win
            self.assertEqual(len(d2["history"]), len(d["history"]) + 1)
        finally:
            shutil.copytree(data_bak, ROOT / "data", dirs_exist_ok=True)
            shutil.rmtree(tmp); shutil.rmtree(data_bak)


if __name__ == "__main__":
    unittest.main()


class EveningScores(unittest.TestCase):
    def _today(self, tmp, ids):
        from tracker.run import todays_games
        mk = lambda gid, home, opp, oid, kind, headline="": {
            "id": gid, "date": "2026-11-04", "start": "2026-11-04T19:00:00-05:00", "time_tbd": False, "home": home,
            "neutral": False, "tv": "ESPN+", "completed": False, "won": None, "score": "", "opp_name": opp,
            "opp_id": oid, "kind": kind, "headline": headline}
        results = {"Duke": {"games": [mk("1", True, "Army", "999", "nonconf")], "w": 1, "l": 0},
                   "Navy": {"games": [mk("2", False, "Virginia", ids["Virginia"], "conf_tourney")], "w": 0, "l": 1},
                   "Siena": {"games": [mk("3", True, "Marist", ids["Marist"], "conf")], "w": 0, "l": 0}}
        owners = {"Duke": ["Kevin B."], "Navy": ["Kevin B."], "Siena": ["Kevin B."]}
        today = todays_games(results, owners, "2026-11-04")
        for g in today["games"]:
            g["line"] = {"1": "DUKE -20.5", "2": "", "3": "SIENA -2"}[g["id"]]
        data = {"updated": "2026-11-04 05:47 EST", "today": today, "yesterday": {"games": []}, "standings": [],
                "teams": {}, "team_info": {}, "history": [], "warnings": []}
        (tmp / "data.json").write_text(json.dumps(data))

    def test_finals_points_and_spreads(self):
        from tracker.run import update_scores
        rows = TM.load_teams()
        ids = {r["team"]: r["espn_id"] or str(5000 + i) for i, r in enumerate(rows)}
        bak = (ROOT / "data" / "teams.csv").read_bytes()
        try:
            for r in rows:
                r["espn_id"] = ids[r["team"]]
            TM.save_teams(rows)
            tmp = Path(tempfile.mkdtemp())
            self._today(tmp, ids)
            board = {
                # Duke won (non-conference) -> +1; game over so its morning line is kept
                "1": {"state": "post", "completed": True, "line": "", "scores": {ids["Duke"]: 81, "999": 60},
                      "winners": {ids["Duke"]: True, "999": False}, "headline": ""},
                # Navy won a conference tournament final -> +2 +5
                "2": {"state": "post", "completed": True, "line": "", "scores": {ids["Navy"]: 70, ids["Virginia"]: 66},
                      "winners": {ids["Navy"]: True, ids["Virginia"]: False}, "headline": "Patriot League Tournament - Final"},
                # Siena hasn't tipped: newer pregame line replaces the morning one
                "3": {"state": "pre", "completed": False, "line": "SIENA -3.5", "scores": {}, "winners": {}, "headline": ""},
            }
            d = update_scores(get_board=lambda day: board, now=dt.datetime(2026, 11, 4, 21, 47), docs=tmp)
            g = {x["id"]: x for x in d["today"]["games"]}
            duke = g["1"]["home"]
            self.assertEqual((g["1"]["completed"], duke["final"], duke["won"], duke["pts"], g["1"]["line"]), (True, 81, True, 1, "DUKE -20.5"))
            self.assertEqual((g["1"]["away"]["final"], g["1"]["away"]["won"]), (60, False))
            navy = g["2"]["away"]
            self.assertEqual((navy["team"], navy["pts"]), ("Navy", 7))
            self.assertEqual((g["3"]["completed"], g["3"]["line"]), (False, "SIENA -3.5"))
            self.assertEqual(d["scores_updated"], "9:47 PM")
            self.assertIn("· as of ${D.scores_updated}", (tmp / "index.html").read_text())
            # a run with nothing new doesn't rewrite the files
            before = (tmp / "data.json").read_text()
            update_scores(get_board=lambda day: board, now=dt.datetime(2026, 11, 4, 22, 47), docs=tmp)
            self.assertEqual((tmp / "data.json").read_text(), before)
        finally:
            (ROOT / "data" / "teams.csv").write_bytes(bak)

    def test_game_points(self):
        from tracker.scoring import game_points
        self.assertEqual(game_points("conf", True), 2)
        self.assertEqual(game_points("conf", False), 0)
        self.assertEqual(game_points("conf_tourney", True, headline="ACC Tournament - Semifinal"), 2)
        self.assertEqual(game_points("ncaa", True, "s16"), 6)
        self.assertEqual(game_points("other_post", True), 0)


class EveningLive(unittest.TestCase):
    def test_live_snapshot_then_final_bumps_records(self):
        from tracker.run import update_scores, _bump, _clock
        self.assertEqual((_bump("3-1", True), _bump("3-1", False), _bump("", True)), ("4-1", "3-2", ""))
        self.assertEqual((_clock("Halftime"), _clock("8:12 - 2nd Half"), _clock("")), ("Halftime", "8:12 2nd", "In progress"))
        rows = TM.load_teams()
        bak = (ROOT / "data" / "teams.csv").read_bytes()
        try:
            for i, r in enumerate(rows):
                r["espn_id"] = r["espn_id"] or str(5000 + i)
            TM.save_teams(rows)
            duke = next(r["espn_id"] for r in rows if r["team"] == "Duke")
            tmp = Path(tempfile.mkdtemp())
            game = {"id": "1", "start": "", "tbd": False, "tv": "", "neutral": False, "completed": False, "kind": "conf",
                    "round": None, "time": "7:00 PM", "line": "DUKE -9.5",
                    "away": {"team": "Army", "pool": False, "home": False, "owners": [], "id": "999", "record": "0-2"},
                    "home": {"team": "Duke", "pool": True, "home": True, "owners": ["Kevin B."], "record": "2-0"}}
            (tmp / "data.json").write_text(json.dumps({"updated": "x", "today": {"date": "2026-11-04", "games": [game]},
                "yesterday": {"games": []}, "standings": [], "teams": {}, "team_info": {}, "history": [], "warnings": []}))
            half = {"1": {"state": "in", "completed": False, "line": "", "detail": "Halftime",
                          "scores": {duke: 40, "999": 31}, "winners": {}, "headline": ""}}
            d = update_scores(get_board=lambda day: half, now=dt.datetime(2026, 11, 4, 20, 7), docs=tmp)
            g = d["today"]["games"][0]
            self.assertEqual((g["live"]["detail"], g["home"]["live"], g["away"]["live"], g["completed"], g["line"]),
                             ("Halftime", 40, 31, False, "DUKE -9.5"))
            self.assertIn("lvclock", (tmp / "index.html").read_text())
            final = {"1": {"state": "post", "completed": True, "line": "", "detail": "Final",
                           "scores": {duke: 77, "999": 70}, "winners": {duke: True, "999": False}, "headline": ""}}
            d = update_scores(get_board=lambda day: final, now=dt.datetime(2026, 11, 4, 21, 7), docs=tmp)
            g = d["today"]["games"][0]
            self.assertNotIn("live", g)
            self.assertEqual((g["home"]["record"], g["away"]["record"], g["home"]["pts"], g["home"]["final"]), ("3-0", "0-3", 2, 77))
            # a later run must not count the result twice
            d = update_scores(get_board=lambda day: final, now=dt.datetime(2026, 11, 4, 22, 7), docs=tmp)
            self.assertEqual(d["today"]["games"][0]["home"]["record"], "3-0")
        finally:
            (ROOT / "data" / "teams.csv").write_bytes(bak)


class Overtime(unittest.TestCase):
    def test_labels(self):
        from tracker.espn import final_label
        from tracker.run import _clock
        self.assertEqual([final_label(x) for x in ["Final", "Final/OT", "Final/2OT", "Final/3OT", ""]],
                         ["Final", "Final OT", "Final 2OT", "Final 3OT", "Final"])
        self.assertEqual((_clock("2:31 - OT"), _clock("0:45 - 2OT")), ("2:31 OT", "0:45 2OT"))

    def test_parse_keeps_status_detail(self):
        ev = {"id": "7", "date": "2026-11-05T00:00Z", "competitions": [{"status": {"type": {"completed": True, "shortDetail": "Final/2OT"}},
              "competitors": [{"id": "150", "winner": True, "score": "99", "team": {"id": "150"}},
                              {"id": "2", "winner": False, "score": "97", "team": {"id": "2"}}]}]}
        self.assertEqual(parse_event(ev, "150", 2)["status_detail"], "Final/2OT")


class MorningCutoff(unittest.TestCase):
    def test_todays_finals_stay_out_of_standings(self):
        from tracker import run as R
        tmp = Path(tempfile.mkdtemp())
        bak = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "data", bak, dirs_exist_ok=True)
        try:
            rows = TM.load_teams()
            for i, r in enumerate(rows):
                r["espn_id"] = str(1000 + i)
            TM.save_teams(rows)
            ids = {r["team"]: r["espn_id"] for r in rows}
            picks = ["Duke", "Michigan", "Kansas St.", "St. John's", "Florida", "Howard", "Navy", "Siena", "Mercyhurst", "SIUE"]
            (ROOT / "data" / "entries.csv").write_text("entry,team\n" + "".join(f"Kevin,{t}\n" for t in picks))

            def sched(tid):
                out = [g("y" + tid, "2026-11-03", True, "999")]                  # yesterday: counts
                if tid == ids["SIUE"]:
                    out.append({**g("t" + tid, "2026-11-04", True, "999"), "home": True})   # finished tonight: doesn't
                return out
            d = R.run(get_schedule=sched, get_team_list=lambda: [], get_lines=lambda day: {},
                      now=dt.datetime(2026, 11, 4, 21, 0), docs=tmp)
            self.assertEqual(d["standings"][0]["total"], 10)
            self.assertEqual(d["teams"]["SIUE"]["total"], 1)
            self.assertEqual((d["teams"]["SIUE"]["w"], d["teams"]["SIUE"]["l"]), (1, 0))
            game = d["today"]["games"][0]
            siue = game["home"] if game["home"]["team"] == "SIUE" else game["away"]
            self.assertEqual((game["completed"], siue["pts"], siue["record"]), (True, 1, "2-0"))
            self.assertEqual(d["through"], "Tue, Nov 3")
            self.assertEqual(d["history"][-1]["totals"]["Kevin"], 10)          # tonight's snapshot = this morning
        finally:
            shutil.copytree(bak, ROOT / "data", dirs_exist_ok=True)
            shutil.rmtree(tmp); shutil.rmtree(bak)


class ScoreboardOverridesStaleSchedule(unittest.TestCase):
    def test_full_run_uses_scoreboard_final(self):
        from tracker import run as R
        tmp, bak = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "data", bak, dirs_exist_ok=True)
        try:
            rows = TM.load_teams()
            for i, r in enumerate(rows):
                r["espn_id"] = str(1000 + i)
            TM.save_teams(rows)
            ids = {r["team"]: r["espn_id"] for r in rows}
            (ROOT / "data" / "entries.csv").write_text("entry,team\n" + "".join(f"Kevin,{t}\n" for t in
                ["Duke", "Michigan", "Kansas St.", "St. John's", "Florida", "Howard", "Navy", "Siena", "Mercyhurst", "SIUE"]))

            def sched(tid):
                out = [g("y" + tid, "2026-11-03", True, "999")]
                if tid == ids["SIUE"]:   # the team schedule still thinks tonight's game is in progress
                    out.append({**g("t1", "2026-11-04", None, "999"), "completed": False, "home": True})
                return out
            board = {"t1": {"state": "post", "completed": True, "line": "", "detail": "Final/OT", "headline": "",
                            "scores": {ids["SIUE"]: 85, "999": 61}, "winners": {ids["SIUE"]: True, "999": False}, "records": {}}}
            d = R.run(get_schedule=sched, get_team_list=lambda: [], get_lines=lambda day: board if day == "2026-11-04" else {},
                      now=dt.datetime(2026, 11, 4, 21, 13), docs=tmp)
            game = d["today"]["games"][0]
            siue = game["home"]
            self.assertEqual((game["completed"], game["final_label"], siue["final"], siue["pts"], siue["record"]),
                             (True, "Final OT", 85, 1, "2-0"))
            self.assertEqual(d["teams"]["SIUE"]["total"], 1)   # still not in the standings until tomorrow
        finally:
            shutil.copytree(bak, ROOT / "data", dirs_exist_ok=True)
            shutil.rmtree(tmp); shutil.rmtree(bak)


class DayRollover(unittest.TestCase):
    def test_after_midnight_is_still_the_previous_evening(self):
        from tracker import run as R
        tmp, bak = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "data", bak, dirs_exist_ok=True)
        try:
            rows = TM.load_teams()
            for i, r in enumerate(rows):
                r["espn_id"] = str(1000 + i)
            TM.save_teams(rows)
            (ROOT / "data" / "entries.csv").write_text("entry,team\n" + "".join(f"Kevin,{t}\n" for t in
                ["Duke", "Michigan", "Kansas St.", "St. John's", "Florida", "Howard", "Navy", "Siena", "Mercyhurst", "SIUE"]))
            sched = lambda tid: [g("a" + tid, "2026-11-03", True, "999"), g("b" + tid, "2026-11-04", True, "999")]
            late = R.run(get_schedule=sched, get_team_list=lambda: [], get_lines=lambda d: {},
                         now=dt.datetime(2026, 11, 5, 0, 10), docs=tmp)          # 12:10 AM Thursday
            self.assertEqual((late["through"], late["today"]["date"], late["standings"][0]["total"]), ("Tue, Nov 3", "2026-11-04", 10))
            morning = R.run(get_schedule=sched, get_team_list=lambda: [], get_lines=lambda d: {},
                            now=dt.datetime(2026, 11, 5, 5, 50), docs=tmp)        # 5:50 AM Thursday
            self.assertEqual((morning["through"], morning["today"]["date"], morning["standings"][0]["total"]), ("Wed, Nov 4", "2026-11-05", 20))
            self.assertEqual(morning["standings"][0]["change"], 10)
        finally:
            shutil.copytree(bak, ROOT / "data", dirs_exist_ok=True)
            shutil.rmtree(tmp); shutil.rmtree(bak)


class SharePreview(unittest.TestCase):
    def test_description(self):
        from tracker.render import share_description, render_html
        one = {"through": "Wed, Nov 4", "standings": [{"rank": 1, "entry": "Mike L.", "full": "Mike LoMauro", "total": 10},
                                                      {"rank": 2, "entry": "Joe H.", "total": 9}]}
        self.assertEqual(share_description(one), "Leader: Mike LoMauro (10 pts) · Standings through Wed, Nov 4")
        tie = {"standings": [{"rank": 1, "entry": e, "total": 3} for e in ["A", "B", "C", "D"]]}
        self.assertEqual(share_description(tie), "Leaders: A & B +2 (3 pts)")
        self.assertEqual(share_description({}), "Season-long standings for the SHU College Hoops Pool")


class EventLabels(unittest.TestCase):
    def test_event_label(self):
        from tracker.run import event_label
        self.assertEqual(event_label("Big East Tournament - Quarterfinal", "conf_tourney"), "Big East Tournament · Quarterfinal")
        self.assertEqual(event_label("Champions Classic", "nonconf"), "Champions Classic")
        self.assertEqual(event_label("Men's Basketball Championship - East Region - Sweet 16", "ncaa"), "East Region")
        self.assertEqual(event_label("Men's Basketball Championship - Final Four", "ncaa"), "")
        self.assertEqual(event_label("", "conf"), "")
