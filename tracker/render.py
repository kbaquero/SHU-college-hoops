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
.mv{font-size:11px;font-weight:600;margin-left:5px;font-variant-numeric:tabular-nums;vertical-align:1px}
.h2sub{text-transform:none;letter-spacing:0;font-weight:400;margin-left:6px}
.game{display:grid;grid-template-columns:76px 1fr auto;gap:4px 12px;padding:10px 14px;border-bottom:1px solid var(--line);align-items:start}
.game:last-child{border-bottom:0}
.gtime{font-variant-numeric:tabular-nums;font-weight:600;padding-top:1px;white-space:nowrap}
.gtv{color:var(--mute);font-size:12px;text-align:right;padding-top:2px}
.line{display:block;color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}
.side{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 8px}
.side+.side{margin-top:3px}
.side .nm{font-weight:400;color:var(--mute)}
.side.pool .nm{font-weight:650;color:var(--ink)}
.own{font-size:12px;color:var(--accent);font-weight:500}
.at{font-size:12px;color:var(--mute);margin-right:2px}
.empty{padding:12px 14px;color:var(--mute)}
.sc{font-variant-numeric:tabular-nums;color:var(--mute);min-width:1.6em}
.sc.win{color:var(--ink);font-weight:700}
.side.lost .nm{opacity:.75}
.ptsb{font-size:12px;font-weight:600;padding:0 6px;border-radius:4px;background:var(--chip);color:var(--mute);font-variant-numeric:tabular-nums}
.ptsb.pos{color:var(--good)}
.gtime.dim{color:var(--mute);font-weight:400}
.sm{display:none}
@media (max-width:520px){.line{display:inline;margin-right:8px}.lg{display:none}.sm{display:inline}#standings th,#standings>thead th,#standings>tbody>tr.entry-row>td{padding:9px 6px}#standings>thead th:first-child,#standings>tbody>tr.entry-row>td:first-child{padding-left:10px}#standings .rank{width:auto;padding-right:0!important;white-space:nowrap}#standings>tbody>tr.entry-row>td:nth-child(2),#standings>thead th:nth-child(2){padding-left:6px;padding-right:2px}#standings>thead th:nth-child(3){width:52px}#standings>thead th:nth-child(4){width:46px}#standings>thead th:nth-child(5){width:56px}#standings>tbody>tr.entry-row>td:nth-child(2){white-space:normal}.game{grid-template-columns:5.3em 1fr}.gtv{grid-column:2;text-align:left;padding-top:0}}
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
.games td{font-size:12px;padding:3px 12px}
svg text{fill:var(--mute);font-size:11px}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12px;color:var(--mute);padding:0 12px 12px}
.legend i{display:inline-block;width:10px;height:3px;border-radius:2px;margin-right:5px;vertical-align:middle}
</style>
</head>
<body>
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
<p class="sub">From this morning's update, so it won't show live scores or line moves. Times are Eastern. Spreads come from ESPN and are missing for games without a posted line.</p>

<h2>Yesterday's games <span class="h2sub" id="yesterday-label"></span></h2>
<div class="card" id="yesterday"></div>
<p class="sub">Final scores with the pool points each picked team earned.</p>

<h2>Points over time</h2>
<div class="card"><div id="chart"></div></div>

<h2>Teams</h2>
<div class="card scroll"><table id="teams"><thead><tr>
</tr></thead><tbody></tbody></table></div>
<p class="sub">Tap a column header to sort, and tap it again to reverse. Reg = non-conference wins ×1 + conference wins ×2. Conf T = conference tournament wins ×2, +5 for the title. NCAA = seed points + round wins. Results from ESPN; disputes go by ncaa.com.</p>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
const D = JSON.parse(document.getElementById('data').textContent);
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
$('#updated').textContent = 'Updated ' + D.updated;
if (D.warnings.length) $('#warnings').innerHTML = '<div class="warn"><b>Needs attention</b><ul>' + D.warnings.map(w => '<li>' + esc(w) + '</li>').join('') + '</ul></div>';

const T = D.teams, I = D.team_info;
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
function gameList(td, el, labelEl, emptyMsg, finals) {
  td = td || {games: []};
  labelEl.textContent = td.label ? '· ' + td.label : '';
  if (!td.games.length) { el.innerHTML = `<div class="empty">${emptyMsg}</div>`; return; }
  const side = (s, prefix, g) => {
    const own = s.pool ? `<span class="own">${esc(s.owners.join(', '))}</span>` : '';
    let sc = '', pts = '';
    if (g.completed && s.final != null) sc = `<span class="sc${s.won ? ' win' : ''}">${s.final}</span>`;
    if (g.completed && s.pool) pts = `<span class="ptsb${s.pts > 0 ? ' pos' : ''}">${s.pts > 0 ? '+' + s.pts : 0}</span>`;
    return `<div class="side${s.pool ? ' pool' : ''}${g.completed && !s.won ? ' lost' : ''}">${prefix}<span class="nm">${esc(s.team)}</span>${sc}${pts}${own}</div>`;
  };
  el.innerHTML = td.games.map(g => {
    const when = g.completed ? 'Final' : finals ? 'No result' : esc(g.time);
    const right = finals ? '' : (g.line ? `<span class="line">${esc(g.line)}</span>` : '') + esc(g.tv || '');
    return `<div class="game"><div class="gtime${finals && !g.completed ? ' dim' : ''}">${when}</div><div>` +
      side(g.away, '', g) + side(g.home, `<span class="at">${g.neutral ? 'vs' : 'at'}</span>`, g) +
      `</div><div class="gtv">${right}</div></div>`;
  }).join('');
}
gameList(D.today, $('#today'), $('#today-label'), 'No picked teams play today.', false);
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
const kinds = {nonconf:'Non-conf', conf:'Conf', conf_tourney:'Conf tourney', ncaa:'NCAA', other_post:'Other post'};
const tb = $('#teams tbody'), headRow = $('#teams thead tr');
const rows = Object.keys(I).map(t => {
  const b = z(T[t]), i = I[t];
  const tr = document.createElement('tr'); tr.className = 'entry-row';
  tr.innerHTML = COLS.map(c => `<td${c.num === false ? '' : ' class="n"'}>${c.html(t, b, i)}</td>`).join('');
  const dr = document.createElement('tr'); dr.className = 'detail'; dr.hidden = true;
  const gs = b.games.filter(g => g.completed);
  dr.innerHTML = `<td colspan="${COLS.length}"><div class="scroll"><table class="games"><tbody>` +
    (gs.length ? gs.slice().reverse().map(g => `<tr><td>${g.date}</td><td>${g.won ? '<span class="up">W</span>' : '<span class="down">L</span>'} ${g.score}</td><td>${esc(g.opp_name)}</td><td>${kinds[g.kind]}</td><td class="n">${g.pts ? '+' + g.pts : 0}</td></tr>`).join('') : '<tr><td>No completed games yet</td></tr>') +
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

// chart: top 8 entries over time
(function chart() {
  const H = D.history, el = $('#chart');
  if (H.length < 2) { el.innerHTML = '<p class="sub" style="padding:12px">The chart fills in after a couple of daily updates.</p>'; return; }
  const top = D.standings.slice(0, 8).map(s => s.entry);
  const colors = ['#c2410c', '#2563eb', '#15803d', '#9333ea', '#ca8a04', '#0891b2', '#db2777', '#4b5563'];
  const W = 900, Ht = 260, P = {l: 40, r: 12, t: 12, b: 24};
  const max = Math.max(1, ...H.flatMap(h => top.map(e => h.totals[e] || 0)));
  const x = i => P.l + (W - P.l - P.r) * i / (H.length - 1);
  const y = v => Ht - P.b - (Ht - P.t - P.b) * v / max;
  let s = `<svg viewBox="0 0 ${W} ${Ht}" width="100%" role="img" aria-label="Points over time for the top entries">`;
  for (let k = 0; k <= 4; k++) { const v = Math.round(max * k / 4); s += `<line x1="${P.l}" x2="${W - P.r}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" opacity=".08"/><text x="${P.l - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`; }
  s += `<text x="${P.l}" y="${Ht - 6}">${H[0].date}</text><text x="${W - P.r}" y="${Ht - 6}" text-anchor="end">${H[H.length - 1].date}</text>`;
  top.forEach((e, j) => { s += `<polyline fill="none" stroke="${colors[j]}" stroke-width="2" points="${H.map((h, i) => x(i) + ',' + y(h.totals[e] || 0)).join(' ')}"/>`; });
  el.innerHTML = s + '</svg><div class="legend">' + top.map((e, j) => `<span><i style="background:${colors[j]}"></i>${esc(e)}</span>`).join('') + '</div>';
})();
</script>
</body>
</html>
"""


def render_html(data):
    blob = json.dumps(data).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", blob)
