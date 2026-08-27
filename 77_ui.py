import json
DATA = open("ui_data.json").read()

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>NFL Engine</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0e1117;color:#e6e6e6;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{background:#161b22;border-bottom:1px solid #30363d;padding:0 20px;display:flex;align-items:center;gap:24px}
h1{font-size:16px;font-weight:600;padding:16px 0;letter-spacing:.5px}
nav{display:flex;gap:4px}
nav button{background:none;border:none;color:#8b949e;padding:16px 14px;font-size:13px;cursor:pointer;border-bottom:2px solid transparent}
nav button.on{color:#58a6ff;border-bottom-color:#58a6ff}
#search{margin-left:auto;background:#0d1117;border:1px solid #30363d;color:#e6e6e6;padding:7px 11px;border-radius:6px;width:210px;font-size:13px}
main{padding:20px;max-width:1500px;margin:0 auto}
.teams{display:grid;grid-template-columns:repeat(auto-fill,minmax(78px,1fr));gap:8px}
.teams button{background:#161b22;border:1px solid #30363d;color:#e6e6e6;padding:14px 0;border-radius:8px;cursor:pointer;font-weight:600;font-size:13px}
.teams button:hover{border-color:#58a6ff;color:#58a6ff}
.teams button.on{background:#1f6feb;border-color:#1f6feb;color:#fff}
.bar{display:flex;align-items:center;gap:16px;margin:20px 0 14px;flex-wrap:wrap}
.bar h2{font-size:22px}
.coach{color:#8b949e;font-size:12px}
.coach b{color:#e6e6e6;font-weight:500}
.sub{display:flex;gap:4px;margin:14px 0;border-bottom:1px solid #30363d}
.sub button{background:none;border:none;color:#8b949e;padding:9px 14px;cursor:pointer;font-size:13px;border-bottom:2px solid transparent}
.sub button.on{color:#e6e6e6;border-bottom-color:#f78166}
.grp{margin-bottom:22px}
.grp h3{font-size:11px;text-transform:uppercase;letter-spacing:1.2px;color:#8b949e;margin-bottom:8px}
.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(228px,1fr));gap:8px}
.p{display:flex;align-items:center;gap:10px;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px 10px;cursor:pointer;position:relative}
.p:hover{border-color:#58a6ff}
.p.hurt{border-color:#f85149;background:#2d1518}
.p.hurt:hover{border-color:#ff7b72}
.p.out{opacity:.72}
.p img,.ph{width:38px;height:38px;border-radius:50%;object-fit:cover;background:#21262d;flex:0 0 38px}
.ph{display:flex;align-items:center;justify-content:center;color:#8b949e;font-size:12px;font-weight:600}
.nm{font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mt{font-size:11px;color:#8b949e}
.mt.red{color:#ff7b72;font-weight:500}
.rk{margin-left:auto;background:#21262d;border-radius:5px;padding:2px 7px;font-size:11px;color:#8b949e;flex:0 0 auto}
.rk.s{background:#1f6feb;color:#fff}
.rk.h{background:#f85149;color:#fff}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:#8b949e;font-size:11px;text-transform:uppercase;letter-spacing:1px;padding:8px;border-bottom:1px solid #30363d}
td{padding:9px 8px;border-bottom:1px solid #21262d;vertical-align:top}
tr:hover td{background:#161b22}
.tag{display:inline-block;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:600}
.tag.OUT{background:#f85149;color:#fff}
.tag.PUP{background:#bb8009;color:#fff}
.tag.DOUBTFUL{background:#bb8009;color:#fff}
.tag.QUESTIONABLE{background:#3d2f0a;color:#e3b341;border:1px solid #6b5410}
.injbox{background:#2d1518;border:1px solid #f85149;border-radius:8px;padding:12px 14px;margin-bottom:18px}
.injbox .h{color:#ff7b72;font-weight:600;font-size:13px;margin-bottom:4px}
.injbox .d{color:#c9a2a2;font-size:12px}
.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:50;overflow-y:auto}
.modal.on{display:block}
.box{background:#0d1117;border:1px solid #30363d;border-radius:12px;max-width:780px;margin:40px auto;padding:24px}
.hd{display:flex;align-items:center;gap:16px;margin-bottom:20px}
.hd img,.hd .ph{width:76px;height:76px;flex:0 0 76px}
.hd h2{font-size:22px}
.x{margin-left:auto;background:none;border:1px solid #30363d;color:#8b949e;border-radius:6px;width:30px;height:30px;cursor:pointer;font-size:16px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(105px,1fr));gap:8px;margin-bottom:20px}
.st{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px}
.st .v{font-size:19px;font-weight:600}
.st .l{font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:.8px;margin-top:2px}
.sec{font-size:11px;text-transform:uppercase;letter-spacing:1.2px;color:#8b949e;margin:18px 0 8px}
.none{color:#8b949e;padding:30px;text-align:center}
</style></head><body>
<header><h1>NFL ENGINE</h1>
<nav><button class="on" onclick="tab('rosters')">Rosters</button>
<button onclick="tab('board')">Draft Board</button></nav>
<input id="search" placeholder="Search any player..."></header>
<main>
<div id="rosters"><div class="teams" id="tg"></div><div id="tv"></div></div>
<div id="board" style="display:none"></div>
</main>
<div class="modal" id="md" onclick="if(event.target.id=='md')close_()"><div class="box" id="mb"></div></div>
<script>
const D = __DATA__;
const ORD_OFF=['QB','WR','TE','RB','FB'];
const ORD_DEF=['LDE','RDE','DE','NT','DT','LOLB','ROLB','SLB','MLB','WLB','LB','LCB','RCB','CB','NB','FS','SS','S'];
"""

HTML += """
let TM=null, SIDE='offense';
const $=id=>document.getElementById(id);
const esc=s=>String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const ini=n=>String(n||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase();
const pic=(p,c)=>p.img?`<img class="${c||''}" src="${p.img}" onerror="this.outerHTML='<div class=ph>${ini(p.name)}</div>'">`:`<div class="ph ${c||''}">${ini(p.name)}</div>`;
const order=(keys,ref)=>keys.slice().sort((a,b)=>{
  const i=ref.indexOf(a), j=ref.indexOf(b);
  return (i<0?99:i)-(j<0?99:j) || a.localeCompare(b);});

function tab(t){
  ['rosters','board'].forEach(x=>$(x).style.display = x==t?'':'none');
  document.querySelectorAll('nav button').forEach((b,i)=>b.classList.toggle('on',(i==0)==(t=='rosters')));
  if(t=='board') board();
}
function init(){
  $('tg').innerHTML = Object.keys(D.teams).sort().map(t=>`<button onclick="team('${t}')" id="t_${t}">${t}</button>`).join('');
  team(Object.keys(D.teams).sort()[0]);
}
function team(t){
  TM=t;
  document.querySelectorAll('.teams button').forEach(b=>b.classList.remove('on'));
  $('t_'+t).classList.add('on');
  const c=D.teams[t].coach||{}, b=[];
  if(c.head_coach) b.push(`HC <b>${esc(c.head_coach)}</b>`);
  if(c.off_coordinator) b.push(`OC <b>${esc(c.off_coordinator)}</b>`);
  if(c.def_coordinator) b.push(`DC <b>${esc(c.def_coordinator)}</b>`);
  if(c.scheme_note) b.push(esc(c.scheme_note));
  const iv=D.teams[t].injuries||[];
  $('tv').innerHTML=`<div class="bar"><h2>${t}</h2>
    <div class="coach">${b.length?b.join(' &nbsp;·&nbsp; '):'coaching staff not set &mdash; fill in coaching_2026.csv'}</div></div>
    <div class="sub">
      <button onclick="side('offense')" id="s_offense">Offense</button>
      <button onclick="side('defense')" id="s_defense">Defense</button>
      <button onclick="side('special')" id="s_special">Special Teams</button>
      <button onclick="side('inj')" id="s_inj">Injuries${iv.length?' ('+iv.length+')':''}</button>
    </div><div id="dc"></div>`;
  side(SIDE);
}
function injOf(id){ if(!id) return null; const p=D.players[id]; return p&&p.injury?p.injury:null; }

function side(s){
  SIDE=s;
  document.querySelectorAll('.sub button').forEach(b=>b.classList.remove('on'));
  const el=$('s_'+s); if(el) el.classList.add('on');
  const iv=D.teams[TM].injuries||[];
  if(s=='inj'){
    $('dc').innerHTML = iv.length
      ? `<table><tr><th>Player</th><th>Pos</th><th>Status</th><th>Injury</th><th>Expected timeline</th><th>What it usually costs</th></tr>`+
        iv.map(i=>`<tr onclick="${i.id?`open_('${i.id}')`:''}" style="cursor:pointer">
          <td style="color:#ff7b72;font-weight:500">${esc(i.name)}</td><td>${esc(i.pos)}</td>
          <td><span class="tag ${esc(i.status)}">${esc(i.status)}</span></td>
          <td>${esc(i.inj)}</td><td>${esc(i.timeline)||'&mdash;'}</td>
          <td style="color:#8b949e">${esc(i.desc)||'&mdash;'}</td></tr>`).join('')+`</table>`
      : `<div class="none">No injuries listed.<br>Add rows to injuries_2026.csv and re-run 76_injuries.py</div>`;
    return;
  }
  const g=D.teams[TM].depth[s]||{};
  const ref = s=='offense'?ORD_OFF : s=='defense'?ORD_DEF : [];
  const keys = order(Object.keys(g), ref);
  const hurt = iv.length ? `<div class="injbox"><div class="h">${iv.length} player${iv.length>1?'s':''} on the injury report</div>
     <div class="d">${iv.map(i=>esc(i.name)+' ('+esc(i.inj)+', '+esc(i.status).toLowerCase()+')').join(' &nbsp;·&nbsp; ')}</div></div>` : '';
  $('dc').innerHTML = hurt + (keys.length ? keys.map(pos=>`<div class="grp"><h3>${esc(pos)}</h3><div class="row">`+
    g[pos].map(p=>{
      const d=D.players[p.id]||{}, inj=injOf(p.id);
      const out = inj && (inj.status=='OUT'||inj.status=='PUP');
      const sub = inj ? `<div class="mt red">${esc(inj.inj)} &mdash; ${esc(inj.timeline||inj.status.toLowerCase())}</div>`
        : `<div class="mt">${d.proj!=null?d.proj.toFixed(1)+' proj ppg':(d.ppg!=null?d.ppg.toFixed(1)+' ppg':'&mdash;')}</div>`;
      return `<div class="p ${inj?'hurt':''} ${out?'out':''}" onclick="open_('${p.id}')">${pic(p)}
        <div style="min-width:0"><div class="nm">${esc(p.name)}</div>${sub}</div>
        <span class="rk ${inj?'h':(p.rank==1?'s':'')}">${inj?esc(inj.status[0]):p.rank}</span></div>`;
    }).join('')+`</div></div>`).join('') : `<div class="none">nothing here</div>`);
}
function chart(log){
  if(!log||log.length<2) return '<div class="none">no game log</div>';
  const W=720,H=190,P=30,v=log.map(x=>x.p),mx=Math.max(10,...v);
  const X=i=>P+i*(W-2*P)/(log.length-1), Y=p=>H-P-(p/mx)*(H-2*P);
  const med=[...v].sort((a,b)=>a-b)[Math.floor(v.length/2)];
  const d=log.map((x,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(x.p).toFixed(1)).join(' ');
  const dots=log.map((x,i)=>`<circle cx="${X(i).toFixed(1)}" cy="${Y(x.p).toFixed(1)}" r="2.5" fill="#58a6ff"><title>${x.s} wk${x.w}${x.o?' vs '+x.o:''} — ${x.p} pts</title></circle>`).join('');
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%">
    <line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" stroke="#30363d"/>
    <line x1="${P}" y1="${Y(med)}" x2="${W-P}" y2="${Y(med)}" stroke="#f78166" stroke-dasharray="4 4" opacity=".7"/>
    <text x="${W-P+2}" y="${Y(med)+4}" fill="#f78166" font-size="10">med ${med.toFixed(1)}</text>
    <text x="4" y="${Y(mx)+4}" fill="#8b949e" font-size="10">${mx.toFixed(0)}</text>
    <path d="${d}" fill="none" stroke="#58a6ff" stroke-width="1.8"/>${dots}</svg>`;
}
function open_(id){
  const p=D.players[id]; if(!p) return;
  const pct=x=>x==null?'&mdash;':(100*x).toFixed(0)+'%', num=x=>x==null?'&mdash;':Number(x).toFixed(1);
  const i=p.injury, has=p.games!=null;
  $('mb').innerHTML=`<div class="hd">${pic(p)}
    <div><h2>${esc(p.name)}</h2><div class="mt">${esc(p.team)} &nbsp;·&nbsp; ${esc(p.pos)}${p.rank&&p.rank<90?' #'+p.rank:''}${p.rank==1&&!i?' &nbsp;· STARTER':''}</div></div>
    <button class="x" onclick="close_()">&times;</button></div>
    ${i?`<div class="injbox"><div class="h"><span class="tag ${esc(i.status)}">${esc(i.status)}</span> &nbsp;${esc(i.inj)}${i.timeline?' &mdash; '+esc(i.timeline):''}</div>
      <div class="d">${esc(i.note)}${i.desc?'<br>Historically: '+esc(i.desc)+'.':''}</div></div>`:''}
    ${p.proj!=null?`<div class="sec">Projection</div><div class="stats">
      <div class="st"><div class="v">${num(p.proj)}</div><div class="l">proj ppg</div></div>
      <div class="st"><div class="v">${p.vorp>0?'+':''}${num(p.vorp)}</div><div class="l">vs replacement</div></div>
      <div class="st"><div class="v">${p.value!=null?num(p.value):'&mdash;'}</div><div class="l">value</div></div>
      ${p.exp_games!=null?`<div class="st"><div class="v">${num(p.exp_games)}</div><div class="l">exp games</div></div>`:''}
    </div>`:''}
    ${has?`<div class="sec">Most likely output &amp; odds &mdash; last ${p.games} games</div><div class="stats">
      <div class="st"><div class="v">${num(p.med)}</div><div class="l">median game</div></div>
      <div class="st"><div class="v">${num(p.p25)}&ndash;${num(p.p75)}</div><div class="l">typical range</div></div>
      <div class="st"><div class="v">${num(p.hi)}</div><div class="l">ceiling</div></div>
      <div class="st"><div class="v">${pct(p.p_td)}</div><div class="l">scores a TD</div></div>
      <div class="st"><div class="v">${pct(p.p10)}</div><div class="l">10+ pts</div></div>
      <div class="st"><div class="v">${pct(p.p15)}</div><div class="l">15+ pts</div></div>
      <div class="st"><div class="v">${pct(p.p20)}</div><div class="l">20+ pts</div></div>
      <div class="st"><div class="v">${num(p.sd)}</div><div class="l">volatility</div></div>
    </div><div class="sec">Game by game</div>${chart(p.log)}`
    :`<div class="none">No scoring history &mdash; defensive or special-teams player</div>`}`;
  $('md').classList.add('on');
}
function close_(){$('md').classList.remove('on');}
function board(){
  const r=Object.entries(D.players).filter(([k,p])=>p.value!=null).sort((a,b)=>b[1].value-a[1].value).slice(0,150);
  $('board').innerHTML=`<table><tr><th>#</th><th>Player</th><th>Tm</th><th>Pos</th><th>Proj</th><th>VORP</th><th>Value</th></tr>`+
    r.map(([k,p],i)=>`<tr onclick="open_('${k}')" style="cursor:pointer"><td>${i+1}</td>
      <td style="${p.injury?'color:#ff7b72':''}">${esc(p.name)}${p.injury?' &#9873;':''}</td>
      <td>${esc(p.team)}</td><td>${esc(p.pos)}</td><td>${p.proj==null?'':p.proj.toFixed(1)}</td>
      <td>${p.vorp==null?'':(p.vorp>0?'+':'')+p.vorp.toFixed(1)}</td><td>${p.value.toFixed(1)}</td></tr>`).join('')+`</table>`;
}
$('search').addEventListener('input',e=>{
  const q=e.target.value.toLowerCase().trim(); if(q.length<3) return;
  const h=Object.entries(D.players).find(([k,p])=>String(p.name).toLowerCase().includes(q));
  if(h) open_(h[0]);
});
document.addEventListener('keydown',e=>{if(e.key=='Escape') close_();});
init();
</script></body></html>"""

with open("nfl_engine.html", "w") as f:
    f.write(HTML.replace("__DATA__", DATA))
print("Saved nfl_engine.html")
