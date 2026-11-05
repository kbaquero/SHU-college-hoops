"""Builds the standings page as one self-contained HTML file (data embedded)."""
import json

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SHU College Hoops Pool</title>
<meta name="description" content="Season-long standings for the SHU College Hoops Pool">
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
:root{--bg:#f6f5f1;--card:#fff;--ink:#1b1d21;--mute:#6a6f78;--line:#e3e1da;--accent:#c2410c;--good:#15803d;--bad:#b91c1c;--chip:#f0eee8}
@media (prefers-color-scheme:dark){:root{--bg:#121316;--card:#1b1d22;--ink:#ecebe7;--mute:#9a9fa8;--line:#2c2f36;--accent:#fb923c;--good:#4ade80;--bad:#f87171;--chip:#252830}}
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
#ptr{position:fixed;left:0;right:0;top:0;z-index:10;display:flex;justify-content:center;align-items:center;height:48px;padding-top:env(safe-area-inset-top);transform:translateY(-100%);opacity:0;pointer-events:none}
#ptr .pill{display:flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:13px;font-weight:500;color:var(--ink);box-shadow:0 4px 14px rgba(0,0,0,.12)}
#ptr-icon{display:inline-block;transition:transform .15s}
#ptr.ready #ptr-icon{transform:rotate(180deg)}
#ptr.busy #ptr-icon{animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#standings>thead th:nth-child(n+3),#standings>tbody>tr.entry-row>td:nth-child(n+3){text-align:center}
.mv{font-size:11px;font-weight:600;margin-left:5px;font-variant-numeric:tabular-nums;vertical-align:1px}
.h2sub{text-transform:none;letter-spacing:0;font-weight:400;margin-left:6px}
#yesterday .game{grid-template-columns:48px 1fr}
.game{display:grid;grid-template-columns:84px 1fr;gap:4px 12px;padding:10px 14px;border-bottom:1px solid var(--line);align-items:start}
.game:last-child{border-bottom:0}
.gtime{font-variant-numeric:tabular-nums;font-weight:600;padding-top:1px;white-space:nowrap}
.gline{font-size:12px;font-weight:600;font-variant-numeric:tabular-nums;margin-top:6px}
.gtv{color:var(--mute);font-size:12px;margin-top:2px}
.gline,.gtv{overflow-wrap:anywhere}
.gtype{margin:7px 0 0 24px;line-height:1}
.lvclock{display:block;color:var(--accent);font-size:13px;white-space:normal}
.lvasof{display:block;color:var(--mute);font-size:11px;font-weight:400;margin-top:1px}
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
@media (max-width:520px){.lg{display:none}.sm{display:inline}#standings th,#standings>thead th,#standings>tbody>tr.entry-row>td{padding:9px 6px}#standings>thead th:first-child,#standings>tbody>tr.entry-row>td:first-child{padding-left:10px}#standings .rank{width:auto;padding-right:0!important;white-space:nowrap}#standings>tbody>tr.entry-row>td:nth-child(2),#standings>thead th:nth-child(2){padding-left:6px;padding-right:2px}#standings>thead th:nth-child(3){width:52px}#standings>thead th:nth-child(4){width:46px}#standings>thead th:nth-child(5){width:56px}#standings>tbody>tr.entry-row>td:nth-child(2){white-space:normal}.game{grid-template-columns:5.6em 1fr}#yesterday .game{grid-template-columns:3.2em 1fr}}
.rank{width:44px;color:var(--mute);font-variant-numeric:tabular-nums}
.tot{font-weight:700;font-size:16px}
.up{color:var(--good)}.down{color:var(--bad)}
.entry-row{cursor:pointer}
.entry-row:hover td{background:var(--chip)}
.entry-row td:first-child::before{content:"▸ ";color:var(--mute)}
.entry-row.open td:first-child::before{content:"▾ "}
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
<div id="warnings"></div>

<h2>Standings</h2>
<div class="card scroll"><table id="standings"><thead><tr>
<th class="rank">#</th><th>Entry</th><th class="n">Points</th><th class="n"><span class="lg" title="Points gained since the last daily update">Δ since last</span><span class="sm" title="Points gained since the last daily update">Δ</span></th><th class="n">Record</th>
</tr></thead><tbody></tbody></table></div>

<h2>Today's games <span class="h2sub" id="today-label"></span></h2>
<div class="card" id="today"></div>
<p class="sub"><span id="scores-note"></span>Scores update about hourly in the evening; points become official in the next morning's update. Times are Eastern. Spreads are the last pregame line from ESPN and are missing for games without one.</p>

<h2>Yesterday's games <span class="h2sub" id="yesterday-label"></span></h2>
<div class="card" id="yesterday"></div>
<p class="sub">Final scores with the pool points each picked team earned.</p>

<h2>Points over time</h2>
<div class="card"><div id="chart"></div></div>
<p class="sub">Tap names to highlight their lines, and tap again to clear.</p>

<h2>Teams</h2>
<div class="card scroll"><table id="teams"><thead><tr>
</tr></thead><tbody></tbody></table></div>
<p class="sub">Tap a column header to sort, and tap it again to reverse. Reg = non-conference wins ×1 + conference wins ×2. Conf T = conference tournament wins ×2, +5 for the title. NCAA = seed points + round wins. Game types in each team's log: NC non-conference, C conference, CT conference tournament, NCAA NCAA tournament (shown by round: Play-in, R64, R32, S16, E8, F4, Title), PS other postseason (NIT and similar, no points). Results from ESPN; disputes go by ncaa.com.</p>
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
if (D.warnings.length) $('#warnings').innerHTML = '<div class="warn"><b>Needs attention</b><ul>' + D.warnings.map(w => '<li>' + esc(w) + '</li>').join('') + '</ul></div>';

const T = D.teams, I = D.team_info;
const ownList = a => a.map(esc).join('<span class="sep">, </span>');   // names in accent, commas muted
const wl = b => b ? [b.w ?? (b.nonconf_w + b.conf_w + b.ct_w), b.l ?? (b.nonconf_l + b.conf_l + b.ct_l)] : [0, 0];
const rec = b => b ? wl(b).join('-') : '–';
const roundName = {playin:'Play-in', r64:'R64', r32:'R32', s16:'S16', e8:'E8', f4:'F4', final:'Title'};
const mv = m => !m ? '' : m > 0 ? `<span class="mv up" title="Up ${m} since last update">▲${m}</span>` : `<span class="mv down" title="Down ${-m} since last update">▼${-m}</span>`;
const chg = c => c == null ? '<span class="sub">–</span>' : c > 0 ? `<span class="up">+${c}</span>` : c < 0 ? `<span class="down">${c}</span>` : '<span class="sub">0</span>';

// standings
const sb = $('#standings tbody');
D.standings.forEach(s => {
  const W = s.teams.reduce((a, t) => a + wl(T[t])[0], 0), L = s.teams.reduce((a, t) => a + wl(T[t])[1], 0);
  const tr = document.createElement('tr'); tr.className = 'entry-row';
  tr.innerHTML = `<td class="rank">${s.rank}${mv(s.move)}</td><td><b>${esc(s.entry)}</b></td><td class="n tot">${s.total}</td><td class="n">${chg(s.change)}</td><td class="n">${W}-${L}</td>`;
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
  el.innerHTML = td.games.map(g => {
    const when = g.completed ? esc(g.final_label || 'Final') : finals ? 'No result'
      : g.live ? `<span class="lvclock">${esc(g.live.detail)}</span><span class="lvasof">as of ${esc(g.live.as_of)}</span>` : esc(g.time);
    const under = (g.line ? `<div class="gline">${esc(g.line)}</div>` : '') + (!finals && g.tv && !g.completed ? `<div class="gtv">${esc(g.tv)}</div>` : '');
    const label = g.kind === 'ncaa' && roundLong[g.round] ? roundLong[g.round] : kindName[g.kind];
    const type = label ? `<div class="gtype"><span class="tag k-${g.kind}">${esc(label)}</span></div>` : '';
    return `<div class="game"><div class="gleft"><div class="gtime${finals && !g.completed ? ' dim' : ''}">${when}</div>${under}</div><div class="sides">` +
      side(g.away, '', g) + side(g.home, g.neutral ? 'vs' : 'at', g) + type + `</div></div>`;
  }).join('');
}
gameList(D.today, $('#today'), $('#today-label'), 'No picked teams play today.', false);
if (D.scores_updated) $('#scores-note').textContent = `Scores as of ${D.scores_updated}. `;
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
  const tr = document.createElement('tr'); tr.className = 'entry-row';
  tr.innerHTML = COLS.map(c => `<td${c.num === false ? '' : ' class="n"'}>${c.html(t, b, i)}</td>`).join('');
  const dr = document.createElement('tr'); dr.className = 'detail'; dr.hidden = true;
  const gs = b.games.filter(g => g.completed);
  dr.innerHTML = `<td colspan="${COLS.length}"><div class="pickedby">Picked by <span class="own">${i.owners.length ? ownList(i.owners) : '<span class="sep">nobody</span>'}</span></div><div class="scroll"><table class="games"><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th class="n">Pts</th><th>Type</th></tr></thead><tbody>` +
    (gs.length ? gs.slice().reverse().map(g => `<tr><td>${+g.date.slice(5, 7)}/${+g.date.slice(8, 10)}</td><td>${g.home === false && !g.neutral ? '<span class="at">at</span> ' : g.neutral ? '<span class="at">vs</span> ' : ''}${esc(g.opp_name)}</td><td>${g.won ? '<span class="up">W</span>' : '<span class="down">L</span>'} ${g.score}${/OT/i.test(g.status_detail || '') ? ` <span class="sub">${esc((g.status_detail.match(/\d*OT/i) || ['OT'])[0])}</span>` : ''}</td><td class="n">${g.pts ? '+' + g.pts : 0}</td><td>${g.kind === 'ncaa' && roundName[g.round] ? roundName[g.round] : kinds[g.kind]}</td></tr>`).join('') : '<tr><td colspan="5" style="white-space:normal">No completed games yet</td></tr>') +
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
  const ents = D.standings.map(s => s.entry);
  const colors = ['#e8590c', '#1c7ed6', '#2f9e44', '#ae3ec9', '#f08c00', '#0c8599', '#e64980',
                  '#4263eb', '#66a80f', '#c92a2a', '#868e96', '#7950f2', '#a87b4f', '#15aabf'];
  const col = j => colors[j % colors.length];
  const sel = new Set();
  const fmt = d => new Date(d + 'T12:00:00').toLocaleDateString('en-US', {month: 'short', day: 'numeric'});
  function draw() {
    const W = Math.max(280, el.clientWidth), Ht = W < 520 ? 220 : 280, P = {l: 34, r: 14, t: 14, b: 26};
    const raw = Math.max(1, ...H.flatMap(h => ents.map(e => h.totals[e] || 0)));
    const mag = 10 ** Math.floor(Math.log10(raw / 5)), step = [1, 2, 5, 10].map(m => m * mag).find(v => v >= raw / 5) || 1;
    const stepI = Math.max(1, Math.round(step)), max = Math.ceil(raw / stepI) * stepI;
    const x = i => P.l + (W - P.l - P.r) * i / (H.length - 1);
    const y = v => Ht - P.b - (Ht - P.t - P.b) * v / max;
    let s = `<svg width="${W}" height="${Ht}" viewBox="0 0 ${W} ${Ht}" role="img" aria-label="Points over time for every entry">`;
    for (let v = 0; v <= max; v += stepI) { s += `<line x1="${P.l}" x2="${W - P.r}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" opacity=".08"/><text x="${P.l - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`; }
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
    if (b.dataset.clear) sel.clear(); else { const n = b.dataset.e; sel.has(n) ? sel.delete(n) : sel.add(n); }
    draw();
  });
  let rt; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(draw, 120); });
  draw();
})();
</script>
</body>
</html>
"""


def render_html(data):
    blob = json.dumps(data).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", blob)
