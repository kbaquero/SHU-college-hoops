"""Builds the standings page as one self-contained HTML file (data embedded)."""
import html
import json

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SHU College Hoops Pool</title>
<meta name="description" content="__OG_DESC__">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SHU College Hoops Pool">
<meta property="og:title" content="SHU College Hoops Pool">
<meta property="og:description" content="__OG_DESC__">
<meta property="og:url" content="https://kbaquero.github.io/SHU-college-hoops/">
<meta property="og:image" content="https://kbaquero.github.io/SHU-college-hoops/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Basketball icon with the title SHU College Hoops Pool">
<meta name="twitter:card" content="summary_large_image">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/svg+xml" href="icons/icon.svg">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="SHU Hoops">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#f6f5f1" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121316" media="(prefers-color-scheme: dark)">
<style>
:root{--bg:#f6f5f1;--card:#fff;--ink:#1b1d21;--mute:#6a6f78;--line:#e3e1da;--accent:#c2410c;--good:#15803d;--bad:#b91c1c;--chip:#f0eee8;--me:#2563eb;--metint:#e8effd}
@media (prefers-color-scheme:dark){:root{--bg:#121316;--card:#1b1d22;--ink:#ecebe7;--mute:#9a9fa8;--line:#2c2f36;--accent:#fb923c;--good:#4ade80;--bad:#f87171;--chip:#252830;--me:#60a5fa;--metint:#1c2a45}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:960px;margin:0 auto;padding:calc(24px + env(safe-area-inset-top)) max(16px,env(safe-area-inset-right)) calc(64px + env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left))}
h1{font-size:26px;margin:0 0 2px;letter-spacing:-.01em;display:flex;align-items:center;gap:10px}
h1 img{width:34px;height:34px;border-radius:8px}
h2{font-size:15px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin:32px 0 10px}
.sub{color:var(--mute);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
table{width:100%;border-collapse:collapse}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{font-size:12px;color:var(--mute);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:0}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
#teams th button{all:unset;cursor:pointer;white-space:nowrap}
#teams th button:hover,#teams th[aria-sort=ascending] button,#teams th[aria-sort=descending] button{color:var(--ink)}
#teams th button:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}
.arr{font-size:10px}
/* tabs: bottom bar on phones, sticky segmented bar on wide screens */
#tabs{position:fixed;left:0;right:0;bottom:0;z-index:20;display:grid;grid-template-columns:repeat(4,1fr);gap:2px;padding:6px 8px calc(4px + env(safe-area-inset-bottom));
  background:color-mix(in srgb,var(--card) 90%,transparent);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-top:1px solid var(--line)}
#tabs button{all:unset;flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px 0 6px;font-size:11px;font-weight:600;
  color:var(--mute);cursor:pointer;border-radius:10px;-webkit-tap-highlight-color:transparent}
#tabs svg{width:23px;height:23px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
#tabs button[aria-selected=true]{color:var(--accent)}
/* league name under the buttons: lifts them clear of the iPhone home-indicator swipe zone */
.tabfoot{grid-column:1/-1;text-align:center;font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);opacity:.7;padding:6px 0 2px;pointer-events:none;user-select:none;-webkit-user-select:none}
#tabs button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
main{padding-bottom:calc(118px + env(safe-area-inset-bottom))}
.panel>h2:first-child,.panel>#mycard+h2,.panel>#mycard[hidden]+h2{margin-top:22px}
@media (min-width:760px){
  .tabfoot{display:none}
  #tabs{position:sticky;top:0;bottom:auto;margin:18px 0 0;padding:4px;border:1px solid var(--line);border-radius:12px;background:color-mix(in srgb,var(--card) 92%,transparent)}
  #tabs button{flex-direction:row;justify-content:center;gap:8px;font-size:14px;padding:9px 0}
  #tabs svg{width:18px;height:18px}
  #tabs button[aria-selected=true]{background:var(--chip);color:var(--ink)}
  main{padding-bottom:64px}
}
/* summary card for the picked entry */
.mycard{margin:18px 0 4px;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;box-shadow:inset 4px 0 0 var(--me)}
.mc-top{display:flex;align-items:baseline;justify-content:space-between;gap:10px;padding:12px 14px 11px 18px}
.mc-name{font-weight:700;color:var(--me);font-size:17px}
.mc-rank{font-size:15px;font-weight:700;white-space:nowrap}.mc-rank .mv{margin-left:4px}
.mc-stats{display:flex;gap:16px;padding:0 14px 12px 18px;font-size:13px;color:var(--mute)}
.mc-stats b{color:var(--ink);font-size:15px;font-variant-numeric:tabular-nums;margin-right:3px}
.mc-sec{border-top:1px solid var(--line);padding:10px 14px 10px 18px}
.mc-h{display:flex;justify-content:space-between;font-size:11px;font-weight:650;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin-bottom:6px}
.mc-h span:last-child{text-transform:none;letter-spacing:0;font-weight:400}
.mc-g{display:grid;grid-template-columns:minmax(0,1fr) 5.2em 2.3em 4.6em;gap:8px;align-items:baseline;font-size:14px;padding:3px 0}
.mc-g .t{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mc-g .t i{font-style:normal;font-weight:400;color:var(--mute);font-size:12px;margin-left:4px}
.mc-g .s{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}.mc-g .s.lead{font-weight:650}.mc-g .s.trail{color:var(--mute)}
.mc-g .ptsb{justify-self:center;min-width:0}
.mc-g .st{font-size:12px;color:var(--mute);text-align:right;white-space:nowrap}.mc-g .st.live{color:var(--accent)}
@media (max-width:360px){.mc-g{grid-template-columns:minmax(0,1fr) 4.9em 2.2em 4.4em;gap:6px;font-size:13px}
  .mc-g .t{white-space:normal}.mc-g .t i{display:block;margin-left:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}

.viewas{display:flex;align-items:center;gap:8px;margin-top:10px;font-size:13px;color:var(--mute)}
.viewas select{font:inherit;font-size:14px;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:8px;padding:5px 28px 5px 10px;
  appearance:none;-webkit-appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--mute) 50%),linear-gradient(135deg,var(--mute) 50%,transparent 50%);
  background-position:calc(100% - 15px) 52%,calc(100% - 10px) 52%;background-size:5px 5px;background-repeat:no-repeat;max-width:62vw}
.has-me .viewas select{border-color:var(--me);color:var(--me);font-weight:600}
#standings tr.entry-row.me>td{background:var(--metint)}
#standings tr.entry-row.me>td:first-child{box-shadow:inset 3px 0 0 var(--me)}
#standings tr.entry-row.me b{color:var(--me)}
.game.mine{--ow:2px;--oc:color-mix(in srgb,var(--me) 55%,transparent);box-shadow:inset var(--ow) 0 0 var(--oc),inset calc(-1*var(--ow)) 0 0 var(--oc)}
.game.mine.myfirst{box-shadow:inset var(--ow) 0 0 var(--oc),inset calc(-1*var(--ow)) 0 0 var(--oc),inset 0 var(--ow) 0 var(--oc)}
.game.mine.mylast{box-shadow:inset var(--ow) 0 0 var(--oc),inset calc(-1*var(--ow)) 0 0 var(--oc),inset 0 calc(-1*var(--ow)) 0 var(--oc)}
.game.mine.myfirst.mylast{box-shadow:inset 0 0 0 var(--ow) var(--oc)}
.card>.game.mine.myfirst:first-child{border-top-left-radius:10px;border-top-right-radius:10px}
.card>.game.mine.mylast:last-child{border-bottom-left-radius:10px;border-bottom-right-radius:10px}
.o.me{color:var(--me);background:var(--metint);border-radius:4px;padding:0 4px;margin:0 -1px;font-weight:650}
#teams tr.entry-row.mine>td{background:var(--metint)}
#teams tr.entry-row.mine>td:first-child{box-shadow:inset 3px 0 0 var(--me)}
h2.withnote{margin-bottom:2px}
.h2note{font-size:13px;color:var(--mute);margin:0 0 10px}
#standings .detail th:not(:first-child),#standings .detail td:not(:first-child){text-align:center}
@media (max-width:350px){#standings>tbody>tr.entry-row>td{font-size:13px}#standings .tot{font-size:14px}#standings .mvc{width:2.1em;padding-left:4px}}
.notes{font-size:13px;color:var(--mute);margin-top:10px;line-height:1.5}
.notes p{margin:0 0 8px}
.notes .nh{margin:12px 0 4px;font-size:11px;font-weight:650;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
.notes dl{display:grid;grid-template-columns:max-content 1fr;gap:3px 12px;margin:0 0 4px}
.notes dt{font-weight:600;color:var(--ink);font-variant-numeric:tabular-nums}
.notes dd{margin:0}
.notes .src{margin-top:12px}
#ptr{position:fixed;left:0;right:0;top:0;z-index:10;display:flex;justify-content:center;align-items:center;height:48px;padding-top:env(safe-area-inset-top);transform:translateY(-100%);opacity:0;pointer-events:none}
#ptr .pill{display:flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:13px;font-weight:500;color:var(--ink);box-shadow:0 4px 14px rgba(0,0,0,.12)}
#ptr-icon{display:inline-block;transition:transform .15s}
#ptr.ready #ptr-icon{transform:rotate(180deg)}
#ptr.busy #ptr-icon{animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#standings>thead th:nth-child(n+3),#standings>tbody>tr.entry-row>td:nth-child(n+3){text-align:center}
.mv{font-size:11px;font-weight:600;font-variant-numeric:tabular-nums;vertical-align:1px}
.rk{display:inline-block;width:24px;text-align:center}
.mvc{display:inline-block;width:2.2em;padding-left:5px;white-space:nowrap}
.h2sub{text-transform:none;letter-spacing:0;font-weight:400;margin-left:6px}
.game{display:grid;grid-template-columns:84px 1fr;gap:4px 12px;padding:10px 14px;border-bottom:1px solid var(--line);align-items:start}
.game:last-child{border-bottom:0}
.narrow .game{grid-template-columns:3.2em 1fr}
.narrow.ot .game{grid-template-columns:4.6em 1fr}
.gtime{font-variant-numeric:tabular-nums;font-weight:600;padding-top:1px;white-space:nowrap}
.gsite,.gevent{font-size:11px;color:var(--mute);line-height:1.3;margin-top:4px;overflow-wrap:break-word;hyphens:auto}
.gevent{color:var(--ink);font-weight:500}
.gsite+.gevent{margin-top:1px}
.gline{font-size:12px;font-weight:600;font-variant-numeric:tabular-nums;margin-top:6px}
.gtv{color:var(--mute);font-size:12px;margin-top:2px}
.gline,.gtv{overflow-wrap:anywhere}
.gtype{margin:7px 0 0 24px;line-height:1}
.lvclock{display:block;color:var(--accent);font-size:13px;white-space:normal}
.sc.lv{color:var(--mute)}
.sc.lv.lead{color:var(--ink);font-weight:600}
.tag{display:inline-block;font-size:10px;font-weight:650;text-transform:uppercase;letter-spacing:.06em;padding:4px 7px;border-radius:4px;
  color:var(--tagc,var(--mute));background:color-mix(in srgb,var(--tagc,var(--mute)) 13%,transparent)}
.k-nonconf{--tagc:var(--mute)}
.k-conf{--tagc:#2563eb}
.k-conf_tourney{--tagc:#7c3aed}
.k-ncaa{--tagc:#a16207}
.k-other_post{--tagc:var(--mute)}
@media (prefers-color-scheme:dark){.k-conf{--tagc:#60a5fa}.k-conf_tourney{--tagc:#a78bfa}.k-ncaa{--tagc:#facc15}}
.game>div{min-width:0}
.trec{font-size:11px;font-weight:400;color:var(--mute);margin-left:5px;font-variant-numeric:tabular-nums;white-space:nowrap}
.sides{max-width:440px}
.side{display:grid;grid-template-columns:18px minmax(0,1fr);column-gap:6px;align-items:baseline}
.side.fin{grid-template-columns:18px minmax(0,1fr) auto 2.3em}
.side+.side{margin-top:4px}
.side .own{grid-column:2 / -1;margin-top:1px}
.side .sc{text-align:right;min-width:1.8em}
.side .ptsb{justify-self:start}
.side .nm{font-weight:400;color:var(--mute)}
.side.pool .nm{font-weight:650;color:var(--ink)}
.own{font-size:12px;color:var(--accent);font-weight:500}
.own .sep{color:var(--mute);font-weight:400}
.at{font-size:12px;color:var(--mute);margin-right:2px}
.empty{padding:12px 14px;color:var(--mute)}
.pickedby{padding:8px 12px 4px;font-size:12px;color:var(--mute);white-space:normal}
#teams .detail .pickedby,#teams .detail .scroll{position:sticky;left:0;max-width:min(926px,calc(100vw - 34px - env(safe-area-inset-left) - env(safe-area-inset-right)))}.pickedby .own{font-size:13px}
.sc{font-variant-numeric:tabular-nums;color:var(--mute);min-width:1.6em}
.sc.win{color:var(--ink);font-weight:700}
.side.lost .nm{opacity:.75}
.ptsb{font-size:12px;font-weight:600;padding:0 6px;border-radius:4px;background:var(--chip);color:var(--mute);font-variant-numeric:tabular-nums}
.ptsb.pos{color:var(--good)}
.gtime.dim{color:var(--mute);font-weight:400}
.sm{display:none}
@media (max-width:520px){.lg{display:none}.sm{display:inline}#standings th,#standings>thead th,#standings>tbody>tr.entry-row>td{padding:9px 6px}#standings>thead th:first-child,#standings>tbody>tr.entry-row>td:first-child{padding-left:10px}#standings .rank{width:auto;padding-right:0!important;white-space:nowrap}#standings>tbody>tr.entry-row>td:nth-child(2),#standings>thead th:nth-child(2){padding-left:6px;padding-right:2px}#standings>thead th:nth-child(3){width:48px}#standings>thead th:nth-child(4){width:34px}#standings>thead th:nth-child(5){width:50px}#standings>tbody>tr.entry-row>td:nth-child(2){white-space:normal}.game{grid-template-columns:5.6em 1fr}}
.rank{width:44px;color:var(--mute);font-variant-numeric:tabular-nums}
.tot{font-weight:700;font-size:16px}
.up{color:var(--good)}.down{color:var(--bad)}
.entry-row{cursor:pointer}
.entry-row:hover td{background:var(--chip)}
.entry-row.open>td{background:var(--chip)}
.detail td{background:var(--chip);padding:0}
#standings .detail .scroll{max-width:min(926px,calc(100vw - 34px - env(safe-area-inset-left) - env(safe-area-inset-right)))}
.detail table th,.detail table td{padding:6px 12px;font-size:13px}
.scroll{overflow-x:auto}
.chip{display:inline-block;background:var(--chip);border-radius:4px;padding:0 6px;font-size:12px;color:var(--mute)}
.warn{background:color-mix(in srgb,var(--accent) 10%,var(--card));border:1px solid color-mix(in srgb,var(--accent) 35%,var(--line));border-radius:10px;padding:10px 14px;font-size:13px;margin-top:16px}
.warn ul{margin:4px 0 0;padding-left:18px}
.detail .games td{font-size:12px;padding:4px 12px}
.detail .games th{font-size:10px;padding:6px 12px 3px}
@media (max-width:520px){.detail .games th,.detail .games td{padding-left:5px;padding-right:5px}.detail .games th:first-child,.detail .games td:first-child{padding-left:12px}.detail .games th:last-child,.detail .games td:last-child{padding-right:12px}.detail .games td:nth-child(2){white-space:normal;min-width:6em}}
svg text{fill:var(--mute);font-size:11px}
#chart{padding-top:4px}
#chart svg{display:block}
#value svg{display:block;touch-action:manipulation}
#value text{font-size:11px;fill:var(--mute)}
.vkey{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;color:var(--mute);padding:0 12px 4px}
.vkey i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:-1px}
.vkey i.dash{width:16px;height:0;border-radius:0;border-top:2px dashed var(--mute);vertical-align:3px}
.vinfo{border-top:1px solid var(--line);padding:9px 12px 11px;font-size:13px;color:var(--mute);min-height:20px}
.vinfo b{color:var(--ink)}

.legend{display:flex;flex-wrap:wrap;gap:4px 6px;font-size:12px;padding:2px 10px 12px}
.legend button{all:unset;cursor:pointer;color:var(--ink);padding:3px 7px;border-radius:5px;border:1px solid transparent;white-space:nowrap}
.legend button:hover{background:var(--chip)}
.legend button:focus-visible{outline:2px solid var(--accent)}
.legend button.on{border-color:var(--line);background:var(--chip);font-weight:600}
.legend button.off{color:var(--mute);opacity:.6}
.legend button.clear{color:var(--accent);font-weight:600}
.legend i{display:inline-block;width:12px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle}
</style>
</head>
<body>
<div id="ptr" aria-hidden="true"><div class="pill"><span id="ptr-icon">↓</span><span id="ptr-text">Pull to refresh</span></div></div>
<main>
<h1><img src="icons/icon-180.png" alt="">SHU College Hoops Pool</h1>
<div class="sub" id="updated"></div>
<div class="viewas"><label for="me">Viewing as</label><select id="me"><option value="">Pick your entry…</option></select></div>
<div id="warnings"></div>

<nav id="tabs" aria-label="Sections" role="tablist"><button type="button" data-tab="standings" role="tab"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 20V10M12 20V4M18 20v-7" /></svg><span>Standings</span></button><button type="button" data-tab="games" role="tab"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5v17M6.3 5.8c2.6 3.2 2.6 9.2 0 12.4M17.7 5.8c-2.6 3.2-2.6 9.2 0 12.4"/></svg><span>Games</span></button><button type="button" data-tab="teams" role="tab"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 3H6c0 3.2-.8 5.2-2 6.3V21h16V9.3c-1.2-1.1-2-3.1-2-6.3h-2.5c0 2-1.6 3.6-3.5 3.6S8.5 5 8.5 3z"/></svg><span>Teams</span></button><button type="button" data-tab="trends" role="tab"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 17l5-6 4 3 7-8"/><path d="M15 6h5v5"/></svg><span>Trends</span></button><div class="tabfoot" aria-hidden="true">SHU College Hoops Pool · 2026–27</div></nav>

<section class="panel" data-panel="standings">
<div id="mycard" hidden></div>
<h2 class="withnote">Standings</h2>
<div class="h2note" id="standings-label"></div>
<div class="card scroll"><table id="standings"><thead><tr>
<th class="rank"><span class="rk">#</span></th><th>Entry</th><th class="n">Points</th><th class="n"><span class="lg" title="Points gained since the last daily update">Δ since last</span><span class="sm" title="Points gained since the last daily update">Δ</span></th><th class="n">Record</th>
</tr></thead><tbody></tbody></table></div>

</section>

<section class="panel" data-panel="games">
<h2>Today's games <span class="h2sub" id="today-label"></span></h2>
<div class="card" id="today"></div>
<p class="sub">Scores update about hourly in the evening; points become official in the next morning's update. Times are Eastern. Spreads are the last pregame line from ESPN and are missing for games without one.</p>

<h2>Yesterday's games <span class="h2sub" id="yesterday-label"></span></h2>
<div class="card" id="yesterday"></div>
<p class="sub">Final scores with the pool points each picked team earned.</p>

</section>

<section class="panel" data-panel="teams">
<h2>Teams</h2>
<div class="card scroll"><table id="teams"><thead><tr>
</tr></thead><tbody></tbody></table></div>
<div class="notes">
  <p>Tap a column header to sort, and tap it again to reverse. Tap a team to see its game log.</p>
  <p class="nh">Points</p>
  <dl>
    <dt>Reg</dt><dd>Non-conference wins ×1, conference wins ×2</dd>
    <dt>Conf T</dt><dd>Conference tournament wins ×2, +5 for the title</dd>
    <dt>NCAA</dt><dd>Seed points + tournament wins:<br>
      Seed: 1 → 8 · 2–4 → 6 · 5–8 → 4 · 9–16 → 2<br>
      Wins: Play-in or R64 → 2 · R32 → 4 · S16 → 6 · E8 → 8 · F4 → 10 · Title → 12</dd>
  </dl>
  <p class="nh">Game types in the log</p>
  <dl>
    <dt>vs / at / N</dt><dd>Home / away / neutral site (opponent column)</dd>
    <dt>NC</dt><dd>Non-conference</dd>
    <dt>C</dt><dd>Conference</dd>
    <dt>CT</dt><dd>Conference tournament</dd>
    <dt>R64…</dt><dd>NCAA tournament, shown by round: Play-in, R64, R32, S16, E8, F4, Title</dd>
    <dt>PS</dt><dd>Other postseason (NIT and similar), no points</dd>
  </dl>
  <p class="src">Results from ESPN. Disputes go by ncaa.com.</p>
</div>
</section>

<section class="panel" data-panel="trends">
<h2>Points over time</h2>
<div class="card"><div id="chart"></div></div>
<p class="sub">Tap names to highlight their lines, and tap again to clear.</p>
<h2>Value</h2>
<div class="card"><div id="value"></div><div id="value-info" class="vinfo">Tap a dot to see the team.</div></div>
<p class="sub">Every picked team: salary vs. points so far. Dots above the dashed line are beating the pool's average points per dollar; below it, falling short. Early in the season most teams sit on top of each other, and they spread out as games pile up.</p>

</section>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});

// Fresh standings without force-closing the app:
// 1) whenever the app comes back on screen, check for a newer update and reload if there is one
// 2) pull down from the top of the page to reload on demand
(function freshness() {
  let lastCheck = Date.now();
  async function checkForUpdate() {
    try {
      const r = await fetch('data.json?t=' + Date.now(), {cache: 'no-store'});
      if (!r.ok) return;
      const fresh = await r.json();
      if (fresh.updated !== D.updated || fresh.scores_updated !== D.scores_updated) location.reload();
    } catch (e) { /* offline: keep showing what we have */ }
  }
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && Date.now() - lastCheck > 30000) { lastCheck = Date.now(); checkForUpdate(); }
  });
  window.addEventListener('pageshow', e => { if (e.persisted) checkForUpdate(); });

  const ptr = document.getElementById('ptr'), txt = document.getElementById('ptr-text');
  const TRIGGER = 70;
  let startY = null, dist = 0, busy = false;
  const show = d => {
    const p = Math.min(d, 110);
    ptr.style.transform = `translateY(${p - 48}px)`;
    ptr.style.opacity = Math.min(1, p / TRIGGER);
    ptr.classList.toggle('ready', d >= TRIGGER);
    txt.textContent = d >= TRIGGER ? 'Release to refresh' : 'Pull to refresh';
  };
  const reset = () => { ptr.style.transition = 'transform .2s, opacity .2s'; ptr.style.transform = ''; ptr.style.opacity = ''; ptr.classList.remove('ready');
                        setTimeout(() => ptr.style.transition = '', 220); };
  window.addEventListener('touchstart', e => {
    if (busy || window.scrollY > 0 || e.touches.length !== 1) { startY = null; return; }
    startY = e.touches[0].clientY; dist = 0;
  }, {passive: true});
  window.addEventListener('touchmove', e => {
    if (startY == null) return;
    const dy = e.touches[0].clientY - startY;
    if (dy <= 0 || window.scrollY > 0) { dist = 0; show(0); return; }
    dist = dy * 0.5;   // resistance, like native pull-to-refresh
    show(dist);
  }, {passive: true});
  window.addEventListener('touchend', () => {
    if (startY == null) return;
    startY = null;
    if (dist >= TRIGGER) {
      busy = true; ptr.classList.remove('ready'); ptr.classList.add('busy'); txt.textContent = 'Refreshing…'; show(TRIGGER);
      ptr.classList.remove('ready');
      setTimeout(() => location.reload(), 250);
    } else reset();
    dist = 0;
  });
})();
const D = JSON.parse(document.getElementById('data').textContent);
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
$('#updated').textContent = 'Updated ' + D.updated;
if (D.through) $('#standings-label').textContent = `Through games of ${D.through} · Updates each morning`;
if (D.warnings.length) $('#warnings').innerHTML = '<div class="warn"><b>Needs attention</b><ul>' + D.warnings.map(w => '<li>' + esc(w) + '</li>').join('') + '</ul></div>';

const T = D.teams, I = D.team_info;
const ownList = a => a.map(n => `<span class="o" data-o="${esc(n)}">${esc(n)}</span>`).join('<span class="sep">, </span>');   // names in accent, commas muted
const wl = b => b ? [b.w ?? (b.nonconf_w + b.conf_w + b.ct_w), b.l ?? (b.nonconf_l + b.conf_l + b.ct_l)] : [0, 0];
const rec = b => b ? wl(b).join('-') : '–';
const roundName = {playin:'Play-in', r64:'R64', r32:'R32', s16:'S16', e8:'E8', f4:'F4', final:'Title'};
const mv = m => !m ? '' : m > 0 ? `<span class="mv up" title="Up ${m} since last update">▲${m}</span>` : `<span class="mv down" title="Down ${-m} since last update">▼${-m}</span>`;
const chg = c => c == null ? '<span class="sub">–</span>' : c > 0 ? `<span class="up">+${c}</span>` : c < 0 ? `<span class="down">${c}</span>` : '<span class="sub">0</span>';

// standings
const sb = $('#standings tbody');
D.standings.forEach(s => {
  const W = s.teams.reduce((a, t) => a + wl(T[t])[0], 0), L = s.teams.reduce((a, t) => a + wl(T[t])[1], 0);
  const tr = document.createElement('tr'); tr.className = 'entry-row'; tr.dataset.entry = s.entry;
  tr.innerHTML = `<td class="rank"><span class="rk">${s.rank}</span><span class="mvc">${mv(s.move)}</span></td><td><b>${esc(s.full || s.entry)}</b></td><td class="n tot">${s.total}</td><td class="n">${chg(s.change)}</td><td class="n">${W}-${L}</td>`;
  const dr = document.createElement('tr'); dr.className = 'detail'; dr.hidden = true;
  dr.innerHTML = `<td colspan="5"><div class="scroll"><table><thead><tr><th>Team</th><th class="n">$</th><th class="n">Record</th><th class="n">Conf</th><th class="n">Reg</th><th class="n">Conf T</th><th class="n">NCAA</th><th class="n">Total</th></tr></thead><tbody>` +
    s.teams.map(t => { const b = T[t]; return `<tr><td>${esc(t)} <span class="chip">${I[t].conf}</span></td><td class="n">${I[t].salary}</td><td class="n">${rec(b)}</td><td class="n">${b ? b.conf_w + '-' + b.conf_l : '–'}</td><td class="n">${b ? b.pts_reg : 0}</td><td class="n">${b ? b.pts_ct : 0}</td><td class="n">${b ? b.pts_ncaa : 0}</td><td class="n"><b>${b ? b.total : 0}</b></td></tr>`; }).join('') +
    `</tbody></table></div></td>`;
  tr.onclick = () => { dr.hidden = !dr.hidden; tr.classList.toggle('open'); };
  sb.append(tr, dr);
});

// game lists (today = upcoming from this morning, yesterday = finals)
const roundLong = {playin:'Play-in', r64:'Round of 64', r32:'Round of 32', s16:'Sweet 16', e8:'Elite Eight', f4:'Final Four', final:'National Championship'};
const kindName = {nonconf:'Non-conference', conf:'Conference', conf_tourney:'Conference tournament', ncaa:'NCAA tournament', other_post:'Postseason'};
function gameList(td, el, labelEl, emptyMsg, finals) {
  td = td || {games: []};
  labelEl.textContent = td.label ? '· ' + td.label : '';
  if (!td.games.length) { el.innerHTML = `<div class="empty">${emptyMsg}</div>`; return; }
  // finals-only lists stay narrow on days without event names; any named event widens the whole list
  el.classList.toggle('narrow', finals && !td.games.some(g => g.event));
  el.classList.toggle('ot', td.games.some(g => /OT/.test(g.final_label || '')));
  // one team: [at] name + record ........ score  pts   (entry names on the line below)
  const side = (s, prefix, g) => {
    const rc = s.record ? `<span class="trec">${esc(s.record)}</span>` : '';
    // score + points cells only exist once a game is final, so upcoming games give names the full width
    const live = !g.completed && g.live;
    const other = s === g.away ? g.home : g.away;
    const sc = live ? `<span class="sc lv${s.live != null && other.live != null && s.live > other.live ? ' lead' : ''}">${s.live ?? ''}</span>`
             : !g.completed ? '' : s.final != null ? `<span class="sc${s.won ? ' win' : ''}">${s.final}</span>` : '<span class="sc"></span>';
    const pts = live ? '<span></span>' : !g.completed ? '' : s.pool ? `<span class="ptsb${s.pts > 0 ? ' pos' : ''}">${s.pts > 0 ? '+' + s.pts : 0}</span>` : '<span></span>';
    const own = s.pool && s.owners.length ? `<div class="own">${ownList(s.owners)}</div>` : '';
    return `<div class="side${s.pool ? ' pool' : ''}${g.completed && !s.won ? ' lost' : ''}${g.completed || live ? ' fin' : ''}">` +
      `<span class="at">${prefix}</span><span class="nm">${esc(s.team)}${rc}</span>${sc}${pts}${own}</div>`;
  };
  el.innerHTML = td.games.map((g, idx) => {
    const when = g.completed ? esc(g.final_label || 'Final') : finals ? 'No result'
      : g.live ? `<span class="lvclock">${esc(g.live.detail)}</span>` : esc(g.time);
    // a named event says enough on its own; "Neutral site" only labels unnamed neutral-site games
    const where = g.event ? `<div class="gevent">${esc(g.event)}</div>` : g.neutral ? '<div class="gsite">Neutral site</div>' : '';
    const under = where + (g.line ? `<div class="gline">${esc(g.line)}</div>` : '') + (!finals && g.tv && !g.completed ? `<div class="gtv">${esc(g.tv)}</div>` : '');
    const label = g.kind === 'ncaa' && roundLong[g.round] ? roundLong[g.round] : kindName[g.kind];
    const type = label ? `<div class="gtype"><span class="tag k-${g.kind}">${esc(label)}</span></div>` : '';
    return `<div class="game" data-idx="${idx}"><div class="gleft"><div class="gtime${finals && !g.completed ? ' dim' : ''}">${when}</div>${under}</div><div class="sides">` +
      side(g.away, '', g) + side(g.home, g.neutral ? 'vs' : 'at', g) + type + `</div></div>`;
  }).join('');
}
gameList(D.today, $('#today'), $('#today-label'), 'No picked teams play today.', false);
// one timestamp for the whole list, once any game has started
if (D.scores_updated && (D.today?.games || []).some(g => g.live || g.completed)) $('#today-label').textContent += ` · as of ${D.scores_updated}`;
gameList(D.yesterday, $('#yesterday'), $('#yesterday-label'), 'No picked teams played yesterday.', true);

// teams: sortable table. Each column: label, sort value, cell html, numeric?, first-click direction
const z = b => b || {nonconf_w:0, nonconf_l:0, conf_w:0, conf_l:0, ct_w:0, ct_l:0, pts_reg:0, pts_ct:0, pts_ncaa:0, total:0, ncaa_w:[], games:[]};
const recVal = (w, l) => w * 1000 - l;   // most wins first, fewer losses breaks ties
const COLS = [
  {label:'Team', num:false, dir:1, val:(t) => t.toLowerCase(),
   html:(t, b) => esc(t) + (b.ct_champ ? ' <span class="chip">Conf champ</span>' : '') + (b.ncaa_w.length ? ' <span class="chip">' + roundName[b.ncaa_w[b.ncaa_w.length - 1]] + '</span>' : '')},
  {label:'Conf', num:false, dir:1, val:(t, b, i) => i.conf, html:(t, b, i) => i.conf},
  {label:'$', dir:-1, val:(t, b, i) => i.salary, html:(t, b, i) => i.salary},
  {label:'Overall', dir:-1, val:(t, b) => recVal(...wl(b)), html:(t, b) => rec(b)},
  {label:'Conf', dir:-1, val:(t, b) => recVal(b.conf_w, b.conf_l), html:(t, b) => `${b.conf_w}-${b.conf_l}`},
  {label:'Conf T', dir:-1, val:(t, b) => recVal(b.ct_w, b.ct_l), html:(t, b) => `${b.ct_w}-${b.ct_l}`},
  {label:'Seed', dir:1, val:(t, b) => b.seed || null, html:(t, b) => b.seed || '–'},
  {label:'Reg pts', dir:-1, val:(t, b) => b.pts_reg, html:(t, b) => b.pts_reg},
  {label:'Conf T pts', dir:-1, val:(t, b) => b.pts_ct, html:(t, b) => b.pts_ct},
  {label:'NCAA pts', dir:-1, val:(t, b) => b.pts_ncaa, html:(t, b) => b.pts_ncaa},
  {label:'Total', dir:-1, val:(t, b) => b.total, html:(t, b) => `<b>${b.total}</b>`},
  {label:'Pts/$', dir:-1, val:(t, b, i) => b.total / i.salary, html:(t, b, i) => (b.total / i.salary).toFixed(1)},
  {label:'Picked', dir:-1, val:(t, b, i) => i.owners.length, html:(t, b, i) => `<span title="${esc(i.owners.join(', '))}">${i.owners.length}</span>`},
];
const kinds = {nonconf:'NC', conf:'C', conf_tourney:'CT', ncaa:'NCAA', other_post:'PS'};
const tb = $('#teams tbody'), headRow = $('#teams thead tr');
const rows = Object.keys(I).map(t => {
  const b = z(T[t]), i = I[t];
  const tr = document.createElement('tr'); tr.className = 'entry-row'; tr.dataset.owners = JSON.stringify(i.owners);
  tr.innerHTML = COLS.map(c => `<td${c.num === false ? '' : ' class="n"'}>${c.html(t, b, i)}</td>`).join('');
  const dr = document.createElement('tr'); dr.className = 'detail'; dr.hidden = true;
  const gs = b.games.filter(g => g.completed);
  dr.innerHTML = `<td colspan="${COLS.length}"><div class="pickedby">Picked by <span class="own">${i.owners.length ? ownList(i.owners) : '<span class="sep">nobody</span>'}</span></div><div class="scroll"><table class="games"><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th class="n">Pts</th><th>Type</th></tr></thead><tbody>` +
    (gs.length ? gs.slice().reverse().map(g => `<tr><td>${+g.date.slice(5, 7)}/${+g.date.slice(8, 10)}</td><td><span class="at"${g.neutral ? ' title="Neutral site"' : ''}>${g.neutral ? 'N' : g.home === false ? 'at' : 'vs'}</span> ${esc(g.opp_name)}</td><td>${g.won ? '<span class="up">W</span>' : '<span class="down">L</span>'} ${g.score}${/OT/i.test(g.status_detail || '') ? ` <span class="sub">${esc((g.status_detail.match(/\d*OT/i) || ['OT'])[0])}</span>` : ''}</td><td class="n">${g.pts ? '+' + g.pts : 0}</td><td>${g.kind === 'ncaa' && roundName[g.round] ? roundName[g.round] : kinds[g.kind]}</td></tr>`).join('') : '<tr><td colspan="5" style="white-space:normal">No completed games yet</td></tr>') +
    `</tbody></table></div></td>`;
  tr.onclick = () => { dr.hidden = !dr.hidden; tr.classList.toggle('open'); };
  return {t, b, i, tr, dr};
});
let sortCol = COLS.findIndex(c => c.label === 'Total'), sortDir = -1;
headRow.innerHTML = COLS.map((c, k) => `<th${c.num === false ? '' : ' class="n"'}><button type="button" data-k="${k}">${c.label}<span class="arr"></span></button></th>`).join('');
function sortTeams() {
  const c = COLS[sortCol], tot = COLS.find(x => x.label === 'Total');
  rows.sort((x, y) => {
    const a = c.val(x.t, x.b, x.i), b = c.val(y.t, y.b, y.i);
    if ((a == null) !== (b == null)) return a == null ? 1 : -1;   // blanks (e.g. no seed yet) always last
    const d = a == null ? 0 : typeof a === 'string' ? a.localeCompare(b) : a - b;
    return d * sortDir || (tot.val(y.t, y.b, y.i) - tot.val(x.t, x.b, x.i)) || x.t.localeCompare(y.t);
  });
  rows.forEach(r => tb.append(r.tr, r.dr));   // moving nodes keeps any expanded rows open
  headRow.querySelectorAll('th').forEach((th, k) => {
    th.setAttribute('aria-sort', k === sortCol ? (sortDir === 1 ? 'ascending' : 'descending') : 'none');
    th.querySelector('.arr').textContent = k === sortCol ? (sortDir === 1 ? ' ▲' : ' ▼') : '';
  });
}
headRow.addEventListener('click', e => {
  const btn = e.target.closest('button'); if (!btn) return;
  const k = +btn.dataset.k;
  if (k === sortCol) sortDir = -sortDir; else { sortCol = k; sortDir = COLS[k].dir; }
  sortTeams();
});
sortTeams();

// chart: every entry over time. Tap names in the legend to highlight them.
(function chart() {
  const H = D.history, el = $('#chart');
  if (H.length < 2) { el.innerHTML = '<p class="sub" style="padding:12px">The chart fills in after a couple of daily updates.</p>'; return; }
  // alphabetical, so the legend is easy to scan and each entry keeps the same color as the standings change
  const ents = D.standings.map(s => s.entry).sort((a, b) => a.localeCompare(b));
  const colors = ['#e8590c', '#1c7ed6', '#2f9e44', '#ae3ec9', '#f08c00', '#0c8599', '#e64980',
                  '#4263eb', '#66a80f', '#c92a2a', '#868e96', '#7950f2', '#a87b4f', '#15aabf'];
  const col = j => colors[j % colors.length];
  const sel = new Set();
  const fmt = d => new Date(d + 'T12:00:00').toLocaleDateString('en-US', {month: 'short', day: 'numeric'});
  function draw() {
    const W = Math.max(280, el.clientWidth), Ht = W < 520 ? 220 : 280, P = {l: 48, r: 14, t: 14, b: 26};
    const raw = Math.max(1, ...H.flatMap(h => ents.map(e => h.totals[e] || 0)));
    const mag = 10 ** Math.floor(Math.log10(raw / 5)), step = [1, 2, 5, 10].map(m => m * mag).find(v => v >= raw / 5) || 1;
    const stepI = Math.max(1, Math.round(step)), max = Math.ceil(raw / stepI) * stepI;
    const x = i => P.l + (W - P.l - P.r) * i / (H.length - 1);
    const y = v => Ht - P.b - (Ht - P.t - P.b) * v / max;
    let s = `<svg width="${W}" height="${Ht}" viewBox="0 0 ${W} ${Ht}" role="img" aria-label="Points over time for every entry">`;
    for (let v = 0; v <= max; v += stepI) { s += `<line x1="${P.l}" x2="${W - P.r}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" opacity=".08"/><text x="${P.l - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`; }
    s += `<text transform="translate(13 ${(P.t + Ht - P.b) / 2}) rotate(-90)" text-anchor="middle">Points</text>`;
    s += `<text x="${P.l}" y="${Ht - 6}">${fmt(H[0].date)}</text><text x="${W - P.r}" y="${Ht - 6}" text-anchor="end">${fmt(H[H.length - 1].date)}</text>`;
    const order = ents.map((e, j) => j).sort((a, b) => sel.has(ents[a]) - sel.has(ents[b]));   // highlighted lines on top
    order.forEach(j => {
      const e = ents[j], on = sel.has(e), dim = sel.size && !on;
      s += `<polyline fill="none" stroke="${col(j)}" stroke-width="${on ? 3.5 : 2}" stroke-linejoin="round" opacity="${dim ? .12 : .9}" points="${H.map((h, i) => x(i) + ',' + y(h.totals[e] || 0)).join(' ')}"><title>${esc(e)}</title></polyline>`;
      if (on) { const v = H[H.length - 1].totals[e] || 0; s += `<circle cx="${x(H.length - 1)}" cy="${y(v)}" r="4" fill="${col(j)}"/>`; }
    });
    el.innerHTML = s + '</svg><div class="legend">' + ents.map((e, j) =>
      `<button type="button" class="${sel.has(e) ? 'on' : sel.size ? 'off' : ''}" data-e="${esc(e)}" aria-pressed="${sel.has(e)}"><i style="background:${col(j)}"></i>${esc(e)}</button>`).join('') +
      (sel.size ? '<button type="button" class="clear" data-clear="1">Show all</button>' : '') + '</div>';
  }
  el.addEventListener('click', e => {
    const b = e.target.closest('.legend button'); if (!b) return;
    touched = true;
    if (b.dataset.clear) sel.clear(); else { const n = b.dataset.e; sel.has(n) ? sel.delete(n) : sel.add(n); }
    draw();
  });
  let touched = false;
  window.chartFollowMe = me => { if (touched) return; sel.clear(); if (me && ents.includes(me)) sel.add(me); draw(); };
  window.chartRedraw = draw;   // the Trends tab redraws on show (a hidden panel has no width)
  let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(draw, 120); });
  draw();
})();

// summary card for the picked entry, at the top of the Standings tab
const ord = n => n + (n % 100 >= 11 && n % 100 <= 13 ? 'th' : ['th', 'st', 'nd', 'rd'][n % 10] || 'th');
function renderMyCard(me) {
  const el = $('#mycard'), s = D.standings.find(x => x.entry === me);
  if (!s) { el.hidden = true; el.innerHTML = ''; return; }
  const tied = D.standings.filter(x => x.rank === s.rank).length > 1;
  // one row per side the entry owns: team · vs/at opponent · score · pts · status
  const rows = (td, finals) => (td?.games || []).flatMap(g => [[g.away, g.home, false], [g.home, g.away, true]]
    .filter(([m]) => m.pool && (m.owners || []).includes(me)).map(([m, o, isHome]) => {
      const live = !g.completed && g.live;
      const vs = g.neutral ? 'vs' : isHome ? 'vs' : 'at';
      let sc = '', cls = '';
      if (g.completed && m.final != null) { sc = `${m.won ? 'W' : 'L'} ${m.final}-${o.final}`; cls = m.won ? 'lead' : 'trail'; }
      else if (live && m.live != null) { sc = `${m.live}-${o.live ?? 0}`; cls = m.live > (o.live ?? 0) ? 'lead' : m.live < (o.live ?? 0) ? 'trail' : ''; }
      const pts = g.completed ? `<span class="ptsb${m.pts > 0 ? ' pos' : ''}">${m.pts > 0 ? '+' + m.pts : 0}</span>` : '<span></span>';
      const st = g.completed ? esc(g.final_label || 'Final') : live ? esc(g.live.detail) : finals ? 'No result' : esc(g.time || '');
      return {pts: g.completed ? (m.pts || 0) : 0,
        html: `<div class="mc-g"><span class="t">${esc(m.team)}<i>${vs} ${esc(o.team)}</i></span><span class="s ${cls}">${sc}</span>${pts}<span class="st${live ? ' live' : ''}">${st}</span></div>`};
    }));
  const today = rows(D.today, false), yest = rows(D.yesterday, true);
  const started = (D.today?.games || []).some(g => g.live || g.completed);
  const sec = (title, right, list) => list.length ? `<div class="mc-sec"><div class="mc-h"><span>${title}</span><span>${right}</span></div>${list.map(r => r.html).join('')}</div>` : '';
  const ysum = yest.reduce((a, r) => a + r.pts, 0);
  el.innerHTML = `<div class="mycard"><div class="mc-top"><span class="mc-name">${esc(s.full || s.entry)}</span><span class="mc-rank">${tied ? 'T-' : ''}${ord(s.rank)}${mv(s.move)}</span></div>` +
    sec('Today', started && D.scores_updated ? 'as of ' + esc(D.scores_updated) : '', today) +
    sec('Yesterday', (ysum > 0 ? '+' : '') + ysum + ' pts', yest) + '</div>';
  el.hidden = false;
}

// value: salary vs points for every picked team, against the pool's average points per dollar
(function valueChart() {
  const el = $('#value'), info = $('#value-info');
  const pts = Object.keys(I).filter(t => I[t].owners.length).map(t => ({t, sal: I[t].salary, pts: z(T[t]).total, own: I[t].owners}));
  if (!pts.length) { el.innerHTML = ''; info.hidden = true; return; }
  const rate = pts.reduce((a, d) => a + d.pts, 0) / pts.reduce((a, d) => a + d.sal, 0);
  let me = '', active = null, placed = [];
  function draw() {
    const W = Math.max(280, el.clientWidth), s0 = Math.min(...pts.map(d => d.sal)) - 1, s1 = Math.max(...pts.map(d => d.sal)) + 1;
    // teams on the same salary and points share a spot: pack them in a small grid around it, the viewer's on top
    const groups = {};
    pts.forEach(d => (groups[d.sal + ':' + d.pts] ||= []).push(d));
    const R = W < 360 ? 3.2 : W < 520 ? 3.6 : 4.2, gap = R * 2 + 1.6;
    const perRow = Math.max(2, Math.floor((W - 48) / (s1 - s0) / gap));
    const half = Math.max(0, ...Object.values(groups).map(l => (Math.ceil(l.length / Math.min(l.length, perRow)) - 1) / 2 * gap)) + R;
    const Ht = (W < 520 ? 230 : 280) + half * 2, P = {l: 48, r: 14, t: 8 + half, b: 36 + half};
    const raw = Math.max(2, ...pts.map(d => d.pts), rate * s1);
    const step = raw <= 5 ? 1 : raw <= 12 ? 2 : raw <= 30 ? 5 : 10, max = Math.ceil(raw / step) * step;
    const x = v => P.l + (W - P.l - P.r) * (v - s0) / (s1 - s0), y = v => Ht - P.b - (Ht - P.t - P.b) * v / max;
    let g = `<svg width="${W}" height="${Ht}" viewBox="0 0 ${W} ${Ht}" role="img" aria-label="Salary versus points for every picked team">`;
    for (let v = 0; v <= max; v += step) g += `<line x1="${P.l}" x2="${W - P.r}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" opacity=".08"/><text x="${P.l - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
    const xs = (s1 - s0) > 12 ? 2 : 1;
    for (let v = Math.ceil(s0 / xs) * xs; v <= s1; v += xs) g += `<text x="${x(v)}" y="${Ht - 26}" text-anchor="middle">$${v}</text>`;
    g += `<text x="${(P.l + W - P.r) / 2}" y="${Ht - 6}" text-anchor="middle">Salary</text>`;
    g += `<text transform="translate(13 ${(P.t + Ht - P.b) / 2}) rotate(-90)" text-anchor="middle">Points</text>`;
    g += `<line x1="${x(s0)}" y1="${y(rate * s0)}" x2="${x(s1)}" y2="${y(rate * s1)}" stroke="currentColor" opacity=".45" stroke-width="1.5" stroke-dasharray="5 4"/>`;
    placed = [];
    Object.values(groups).forEach(list => {
      list.sort((a, b) => a.t.localeCompare(b.t));
      const n = list.length, cols = Math.min(n, perRow), rowsN = Math.ceil(n / cols);
      list.forEach((d, k) => {
        const c = k % cols, r = Math.floor(k / cols), inRow = Math.min(cols, n - r * cols);
        placed.push({d, cx: x(d.sal) + (c - (inRow - 1) / 2) * gap, cy: y(d.pts) - (r - (rowsN - 1) / 2) * gap});
      });
    });
    const mine = p => me && p.d.own.includes(me);
    placed.sort((a, b) => mine(a) - mine(b) || (active === b.d) - (active === a.d));
    placed.forEach(p => {
      const on = mine(p), sel = active === p.d;
      g += `<circle cx="${p.cx.toFixed(1)}" cy="${p.cy.toFixed(1)}" r="${sel ? R + 2 : R}" style="fill:${on ? 'var(--me)' : 'var(--mute)'}" opacity="${on || sel ? 1 : me ? .35 : .6}"${sel ? ' stroke="var(--ink)" stroke-width="1.5"' : ''}/>`;
    });
    el.innerHTML = g + '</svg><div class="vkey">' + (me ? '<span><i style="background:var(--me)"></i>Your teams</span><span><i style="background:var(--mute);opacity:.5"></i>Other picked teams</span>' : '<span><i style="background:var(--mute)"></i>Picked teams</span>') +
      `<span><i class="dash"></i>Pool average (${rate.toFixed(2)} pts per $)</span></div>`;
  }
  function describe(d) {
    if (!d) { info.innerHTML = 'Tap a dot to see the team.'; return; }
    const exp = rate * d.sal, diff = d.pts - exp;
    info.innerHTML = `<b>${esc(d.t)}</b> · $${d.sal} · <b>${d.pts}</b> pt${d.pts === 1 ? '' : 's'} (${diff >= 0 ? '+' : ''}${diff.toFixed(1)} vs. average) · picked by ${ownList(d.own)}`;
    info.querySelectorAll('.o').forEach(n => n.classList.toggle('me', n.dataset.o === me));
  }
  el.addEventListener('click', e => {
    const svg = el.querySelector('svg'); if (!svg) return;
    const b = svg.getBoundingClientRect(), px = e.clientX - b.left, py = e.clientY - b.top;
    let best = null, bd = 18 * 18;   // forgiving hit area: nearest dot within 18px
    placed.forEach(p => { const dd = (p.cx - px) ** 2 + (p.cy - py) ** 2; if (dd < bd) { bd = dd; best = p.d; } });
    active = best === active ? null : best; describe(active); draw();
  });
  window.valueFollowMe = m => { me = m || ''; draw(); describe(active); };
  window.valueRedraw = draw;
  let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(draw, 120); });
  draw();
})();

// "Viewing as": each visitor picks their entry once; it's remembered on this device only (no accounts)
(function viewingAs() {
  const KEY = 'shu-hoops-me', pick = $('#me');
  const store = {get: () => { try { return localStorage.getItem(KEY) || ''; } catch (e) { return ''; } },
                 set: v => { try { v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY); } catch (e) {} }};
  const byName = [...D.standings].sort((a, b) => (a.full || a.entry).localeCompare(b.full || b.entry));
  pick.insertAdjacentHTML('beforeend', byName.map(s => `<option value="${esc(s.entry)}">${esc(s.full || s.entry)}</option>`).join(''));
  function apply(me) {
    document.body.classList.toggle('has-me', !!me);
    document.querySelectorAll('#standings tr.entry-row').forEach(tr => {
      const on = tr.dataset.entry === me;
      tr.classList.toggle('me', on);
      tr.nextElementSibling?.classList.toggle('me', on);
    });
    document.querySelectorAll('.o[data-o]').forEach(n => n.classList.toggle('me', n.dataset.o === me));
    // the viewer's games float to the top of Today's and Yesterday's lists (otherwise original order)
    ['#today', '#yesterday'].forEach(id => {
      const list = $(id), games = [...list.querySelectorAll(':scope > .game')];
      games.sort((x, y) => (!!y.querySelector('.o.me') - !!x.querySelector('.o.me')) || (x.dataset.idx - y.dataset.idx))
           .forEach(g => list.append(g));
      // a heavier divider under the viewer's last game, only when other games follow
      // outline the viewer's block of games: sides on each, top on the first, bottom on the last
      const mine = games.filter(g => g.querySelector('.o.me'));
      games.forEach(g => g.classList.remove('mine', 'myfirst', 'mylast'));
      mine.forEach(g => g.classList.add('mine'));
      if (mine.length) { mine[0].classList.add('myfirst'); mine[mine.length - 1].classList.add('mylast'); }
    });
    document.querySelectorAll('#teams tr.entry-row[data-owners]').forEach(tr => {
      const on = !!me && JSON.parse(tr.dataset.owners).includes(me);
      tr.classList.toggle('mine', on);
      tr.nextElementSibling?.classList.toggle('mine', on);
    });
    window.chartFollowMe?.(me);
    window.valueFollowMe?.(me);
    renderMyCard(me);
  }
  let me = store.get();
  if (me && !D.standings.some(s => s.entry === me)) me = '';   // entry renamed or removed
  pick.value = me;
  apply(me);
  pick.addEventListener('change', () => { me = pick.value; store.set(me); apply(me); });
})();
// tabs: chosen by the link (#games etc.), else the last one used on this device, else Standings
(function tabs() {
  const KEY = 'shu-hoops-tab', names = ['standings', 'games', 'teams', 'trends'];
  const btns = [...document.querySelectorAll('#tabs button')], panels = [...document.querySelectorAll('.panel')];
  let cur = null;
  function show(name, scroll) {
    if (!names.includes(name)) name = 'standings';
    const changed = name !== cur; cur = name;
    btns.forEach(b => b.setAttribute('aria-selected', b.dataset.tab === name));
    panels.forEach(p => p.hidden = p.dataset.panel !== name);
    try { localStorage.setItem(KEY, name); } catch (e) {}
    // links like …/#games open that tab; the hash is then cleared so the browser never jumps to a same-named element
    if (location.hash) history.replaceState(null, '', location.pathname + location.search);
    if (name === 'trends') { window.chartRedraw?.(); window.valueRedraw?.(); }
    if (changed && scroll) window.scrollTo(0, 0);
  }
  let saved = ''; try { saved = localStorage.getItem(KEY) || ''; } catch (e) {}
  show(location.hash.slice(1) || saved, false);
  if (scrollY) scrollTo(0, 0);   // a #standings/#teams link would otherwise land on the same-named table
  btns.forEach(b => b.addEventListener('click', () => show(b.dataset.tab, true)));
  window.addEventListener('hashchange', () => { if (location.hash) show(location.hash.slice(1), true); });
})();
</script>
</body>
</html>
"""


def share_description(data):
    """One line for link previews, e.g. 'Leader: Mike LoMauro (10 pts) · Standings through Wed, Nov 4'."""
    st = data.get("standings") or []
    if not st:
        return "Season-long standings for the SHU College Hoops Pool"
    top = [s for s in st if s["rank"] == 1]
    names = " & ".join(s.get("full") or s["entry"] for s in top[:2]) + (f" +{len(top) - 2}" if len(top) > 2 else "")
    lead = f'{"Leaders" if len(top) > 1 else "Leader"}: {names} ({top[0]["total"]} pts)'
    return lead + (f' · Standings through {data["through"]}' if data.get("through") else "")


def render_html(data):
    blob = json.dumps(data).replace("</", "<\\/")
    return TEMPLATE.replace("__OG_DESC__", html.escape(share_description(data), quote=True)).replace("__DATA__", blob)
