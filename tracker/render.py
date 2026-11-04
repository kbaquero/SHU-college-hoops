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
.rank{width:44px;color:var(--mute);font-variant-numeric:tabular-nums}
.tot{font-weight:700;font-size:16px}
.up{color:var(--good)}.down{color:var(--bad)}
.entry-row{cursor:pointer}
.entry-row:hover td{background:var(--chip)}
.entry-row td:first-child::before{content:"▸ ";color:var(--mute)}
.entry-row.open td:first-child::before{content:"▾ "}
.detail td{background:var(--chip);padding:0}
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
<th class="rank">#</th><th>Entry</th><th class="n">Points</th><th class="n">Since last</th><th class="n">Salary</th><th>Top team</th>
</tr></thead><tbody></tbody></table></div>

<h2>Points over time</h2>
<div class="card"><div id="chart"></div></div>

<h2>Teams</h2>
<div class="card scroll"><table id="teams"><thead><tr>
<th>Team</th><th>Conf</th><th class="n">$</th><th class="n">Overall</th><th class="n">Conf</th><th class="n">Conf T</th><th class="n">Seed</th><th class="n">Reg</th><th class="n">Post</th><th class="n">Total</th><th class="n">Pts/$</th><th class="n">Picked</th>
</tr></thead><tbody></tbody></table></div>
<p class="sub">Reg = non-conference wins ×1 + conference wins ×2. Post = conference tournament (wins ×2, title +5) + NCAA seed and round points. Results from ESPN; official tiebreaks and disputes go by ncaa.com.</p>
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
const rec = b => b ? `${b.nonconf_w + b.conf_w + b.ct_w}-${b.nonconf_l + b.conf_l + b.ct_l}` : '–';
const roundName = {playin:'Play-in', r64:'R64', r32:'R32', s16:'S16', e8:'E8', f4:'F4', final:'Title'};
const post = b => b ? b.pts_ct + b.pts_ncaa : 0;
const chg = c => c == null ? '<span class="sub">–</span>' : c > 0 ? `<span class="up">+${c}</span>` : c < 0 ? `<span class="down">${c}</span>` : '<span class="sub">0</span>';

// standings
const sb = $('#standings tbody');
D.standings.forEach(s => {
  const top = s.teams[0];
  const tr = document.createElement('tr'); tr.className = 'entry-row';
  tr.innerHTML = `<td class="rank">${s.rank}</td><td><b>${esc(s.entry)}</b></td><td class="n tot">${s.total}</td><td class="n">${chg(s.change)}</td><td class="n">${s.salary}</td><td>${top ? esc(top) + ' <span class="chip">' + (T[top]?.total ?? 0) + '</span>' : ''}</td>`;
  const dr = document.createElement('tr'); dr.className = 'detail'; dr.hidden = true;
  dr.innerHTML = `<td colspan="6"><div class="scroll"><table><thead><tr><th>Team</th><th class="n">$</th><th class="n">Record</th><th class="n">Conf</th><th class="n">Reg</th><th class="n">Post</th><th class="n">Total</th></tr></thead><tbody>` +
    s.teams.map(t => { const b = T[t]; return `<tr><td>${esc(t)} <span class="chip">${I[t].conf}</span></td><td class="n">${I[t].salary}</td><td class="n">${rec(b)}</td><td class="n">${b ? b.conf_w + '-' + b.conf_l : '–'}</td><td class="n">${b ? b.pts_reg : 0}</td><td class="n">${post(b)}</td><td class="n"><b>${b ? b.total : 0}</b></td></tr>`; }).join('') +
    `</tbody></table></div></td>`;
  tr.onclick = () => { dr.hidden = !dr.hidden; tr.classList.toggle('open'); };
  sb.append(tr, dr);
});

// teams
const tb = $('#teams tbody');
Object.keys(I).sort((a, b) => (T[b]?.total ?? 0) - (T[a]?.total ?? 0)).forEach(t => {
  const b = T[t], i = I[t];
  const tr = document.createElement('tr'); tr.className = 'entry-row';
  const ncaa = b && b.ncaa_w.length ? ' <span class="chip">' + roundName[b.ncaa_w[b.ncaa_w.length - 1]] + '</span>' : '';
  tr.innerHTML = `<td>${esc(t)}${b && b.ct_champ ? ' <span class="chip">Conf champ</span>' : ''}${ncaa}</td><td>${i.conf}</td><td class="n">${i.salary}</td><td class="n">${rec(b)}</td><td class="n">${b ? b.conf_w + '-' + b.conf_l : '–'}</td><td class="n">${b ? b.ct_w + '-' + b.ct_l : '–'}</td><td class="n">${b && b.seed ? b.seed : '–'}</td><td class="n">${b ? b.pts_reg : 0}</td><td class="n">${post(b)}</td><td class="n"><b>${b ? b.total : 0}</b></td><td class="n">${((b ? b.total : 0) / i.salary).toFixed(1)}</td><td class="n" title="${esc(i.owners.join(', '))}">${i.owners.length}</td>`;
  const dr = document.createElement('tr'); dr.className = 'detail'; dr.hidden = true;
  const kinds = {nonconf:'Non-conf', conf:'Conf', conf_tourney:'Conf tourney', ncaa:'NCAA', other_post:'Other post'};
  const gs = (b ? b.games : []).filter(g => g.completed);
  dr.innerHTML = `<td colspan="12"><div class="scroll"><table class="games"><tbody>` +
    (gs.length ? gs.slice().reverse().map(g => `<tr><td>${g.date}</td><td>${g.won ? '<span class="up">W</span>' : '<span class="down">L</span>'} ${g.score}</td><td>${esc(g.opp_name)}</td><td>${kinds[g.kind]}</td><td class="n">${g.pts ? '+' + g.pts : ''}</td></tr>`).join('') : '<tr><td>No completed games yet</td></tr>') +
    `</tbody></table></div></td>`;
  tr.onclick = () => { dr.hidden = !dr.hidden; tr.classList.toggle('open'); };
  tb.append(tr, dr);
});

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
