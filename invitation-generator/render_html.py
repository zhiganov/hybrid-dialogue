#!/usr/bin/env python3
"""
Render the invitation-generator JSON into a single, navigable, *interactive* HTML page.

Follows Thariq Shihipar's "unreasonable effectiveness of HTML" recommendations:
a long markdown brief doesn't get read or acted on; a navigable HTML artifact does,
and "the trick is always to end with an export." So this page lets the convener
curate (keep / maybe / cut each conversation, drop people who don't fit) and copy
their decisions back out as Markdown (or as a prompt for Claude).

Reads the JSON that generate.py wrote and emits one self-contained HTML file.

Usage:
  python render_html.py --input output/invitations-2026-06-27.json
"""
import argparse
import datetime
import glob
import html
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent

TYPES = {
    "content":    {"label": "Content",    "desc": "a shared topic",      "color": "#1f6b66"},
    "tension":    {"label": "Tension",    "desc": "a live disagreement", "color": "#b14a2e"},
    "process":    {"label": "Process",    "desc": "about the inquiry",   "color": "#3f4691"},
    "relational": {"label": "Relational", "desc": "who meets whom",      "color": "#5c7a33"},
}


def e(s: str) -> str:
    return html.escape(str(s), quote=True)


def render_cards(invs):
    out = []
    for i, inv in enumerate(invs, 1):
        t = inv.get("type", "content")
        meta = TYPES.get(t, TYPES["content"])
        voices = "".join(f"<li>{e(v)}</li>" for v in inv.get("grounded_in", []))
        fits = "".join(
            f'<li><label><input type="checkbox" class="pk" data-name="{e(p["name"])}" checked>'
            f'<span class="name">{e(p["name"])}</span>'
            f'<span class="why">{e(p["why"])}</span></label></li>'
            for p in inv.get("recommended_participants", [])
        )
        arch = "".join(f"<li>{e(a)}</li>" for a in inv.get("archetypes_to_invite", []))
        out.append(f"""
      <article class="conv" data-type="{t}" data-status="keep" id="c{i}" style="--c:{meta['color']}">
        <p class="eyebrow"><span class="dot"></span>{meta['label']} &middot; {meta['desc']}</p>
        <h2 class="conv__title">{e(inv.get('title',''))}</h2>
        <p class="framing">{e(inv.get('framing',''))}</p>
        <div class="block block--voices">
          <h3 class="micro">Grown from</h3>
          <ul class="voices">{voices}</ul>
        </div>
        <div class="block">
          <h3 class="micro">Who fits <span class="hint">(uncheck to drop)</span></h3>
          <ul class="fits">{fits}</ul>
        </div>
        <div class="block">
          <h3 class="micro">Who's missing</h3>
          <ul class="arch">{arch}</ul>
        </div>
        <div class="curate" role="group" aria-label="Curate this conversation">
          <div class="seg" role="radiogroup" aria-label="Decision">
            <button class="seg-btn" data-status="keep" role="radio">Keep</button>
            <button class="seg-btn" data-status="maybe" role="radio">Maybe</button>
            <button class="seg-btn" data-status="cut" role="radio">Cut</button>
          </div>
          <textarea class="note" rows="1" placeholder="Notes &mdash; merge with&hellip;, retitle, add someone&hellip;"></textarea>
        </div>
      </article>""")
    return "\n".join(out)


def render_filters(invs):
    present = [t for t in TYPES if any(v.get("type") == t for v in invs)]
    btns = [f'<button class="f is-active" data-filter="all" aria-pressed="true">'
            f'All <span class="n">{len(invs)}</span></button>']
    for t in present:
        n = sum(1 for v in invs if v.get("type") == t)
        btns.append(
            f'<button class="f" data-filter="{t}" aria-pressed="false" '
            f'style="--c:{TYPES[t]["color"]}">'
            f'<span class="dot"></span>{TYPES[t]["label"]} <span class="n">{n}</span></button>'
        )
    return "\n        ".join(btns), len(present)


def render_notes(notes: str) -> str:
    parts = re.split(r"\((\d+)\)\s*", notes.strip())
    intro = e(parts[0].strip())
    items = ""
    for j in range(1, len(parts) - 1, 2):
        items += f"<li>{e(parts[j+1].strip())}</li>"
    lst = f'<ol class="notes-list">{items}</ol>' if items else ""
    return f'<p class="notes-intro">{intro}</p>{lst}'


CSS = """
:root{
  --paper:#e8eae4; --card:#fbfbf9; --ink:#1a1c19; --muted:#6a6e66;
  --line:#d6d8d1; --c:#1f6b66;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"Hanken Grotesk",system-ui,sans-serif;
  font-size:17px; line-height:1.6; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:50rem; margin:0 auto; padding:0 1.5rem 2rem}
a{color:inherit}

/* hero */
.hero{padding:5rem 0 2rem}
.kicker{font-size:.72rem; letter-spacing:.18em; text-transform:uppercase; color:var(--muted); margin:0 0 1.4rem; font-weight:600}
.hero h1{font-family:"Newsreader",Georgia,serif; font-weight:400; font-size:clamp(2.3rem,6vw,3.6rem); line-height:1.07; letter-spacing:-.01em; margin:0 0 1.1rem}
.hero h1 em{font-style:italic; color:#3a3e37}
.lede{font-size:1.12rem; color:#34382f; max-width:34rem; margin:0 0 2.2rem}
.stats{display:flex; gap:2.2rem; flex-wrap:wrap; border-top:1px solid var(--line); padding-top:1.4rem}
.stat{display:flex; flex-direction:column}
.stat b{font-family:"Newsreader",serif; font-size:1.9rem; font-weight:500; line-height:1}
.stat span{font-size:.78rem; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin-top:.35rem}

/* filters */
.filters{position:sticky; top:0; z-index:5; background:rgba(232,234,228,.86); backdrop-filter:blur(8px); margin:2rem 0 0; padding:.9rem 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); display:flex; gap:.5rem; flex-wrap:wrap}
.f{font:inherit; font-size:.86rem; font-weight:500; cursor:pointer; background:transparent; color:var(--muted); border:1px solid var(--line); border-radius:100px; padding:.35rem .85rem; display:inline-flex; align-items:center; gap:.45rem; transition:color .15s,border-color .15s,background .15s}
.f .n{color:var(--muted); font-variant-numeric:tabular-nums}
.f:hover{color:var(--ink); border-color:#b9bcb3}
.f.is-active{color:#fff; background:var(--ink); border-color:var(--ink)}
.f.is-active .n{color:rgba(255,255,255,.6)}
.f:not([data-filter="all"]).is-active{background:var(--c); border-color:var(--c)}
.dot{width:.5rem; height:.5rem; border-radius:50%; background:var(--c); flex:0 0 auto}
.f.is-active .dot{background:rgba(255,255,255,.85)}

.howto{font-size:.9rem; color:var(--muted); margin:1.3rem 0 0; padding-left:1rem; border-left:2px solid var(--line)}

/* conversation cards */
.feed{margin-top:1.6rem; display:flex; flex-direction:column; gap:1.5rem}
.conv{background:var(--card); border:1px solid var(--line); border-left:3px solid var(--c); border-radius:4px; padding:2rem 2rem 1.4rem; transition:opacity .25s ease}
.conv[data-status="cut"]{opacity:.45}
.conv[data-status="cut"] .conv__title{text-decoration:line-through}
.conv[data-status="maybe"]{border-left-style:dashed}
.eyebrow{margin:0 0 .7rem; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; font-weight:700; color:var(--c); display:flex; align-items:center; gap:.5rem}
.conv__title{font-family:"Newsreader",Georgia,serif; font-weight:400; font-size:clamp(1.5rem,3.2vw,2rem); line-height:1.12; letter-spacing:-.01em; margin:0 0 1rem}
.framing{margin:0 0 1.6rem; color:#33372f}
.block{border-top:1px solid var(--line); padding-top:1.1rem; margin-top:1.1rem}
.micro{margin:0 0 .7rem; font-size:.7rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); font-weight:700}
.micro .hint{text-transform:none; letter-spacing:0; font-weight:500; color:#a6a99f}
ul,ol{margin:0; padding:0; list-style:none}
.voices{display:flex; flex-direction:column; gap:.6rem}
.voices li{font-family:"Newsreader",Georgia,serif; font-style:italic; font-size:1.02rem; color:#41453c; padding-left:1rem; border-left:2px solid var(--c)}
.fits{display:flex; flex-direction:column; gap:.55rem}
.fits label{display:flex; gap:.55rem; align-items:baseline; cursor:pointer}
.fits input{margin:.25rem 0 0; accent-color:var(--c); flex:0 0 auto; cursor:pointer}
.fits .name{font-weight:600}
.fits .why{color:var(--muted)}
.fits li.dropped .name,.fits li.dropped .why{opacity:.4; text-decoration:line-through}
.arch{display:flex; flex-direction:column; gap:.5rem}
.arch li{color:#4a4e45; padding-left:1.1rem; position:relative}
.arch li::before{content:"+"; position:absolute; left:0; color:var(--c); font-weight:700}

/* curation controls */
.curate{border-top:1px solid var(--line); margin-top:1.2rem; padding-top:1.1rem; display:flex; flex-wrap:wrap; gap:.7rem; align-items:flex-start}
.seg{display:inline-flex; border:1px solid var(--line); border-radius:100px; overflow:hidden; background:#fff; flex:0 0 auto}
.seg-btn{font:inherit; font-size:.8rem; font-weight:600; cursor:pointer; border:0; background:transparent; color:var(--muted); padding:.4rem .9rem}
.seg-btn+.seg-btn{border-left:1px solid var(--line)}
.seg-btn.is-on[data-status="keep"]{background:var(--c); color:#fff}
.seg-btn.is-on[data-status="maybe"]{background:#d8a32f; color:#3a2f10}
.seg-btn.is-on[data-status="cut"]{background:#8a8d84; color:#fff}
.note{flex:1 1 13rem; min-height:2.5rem; resize:vertical; font:inherit; font-size:.92rem; line-height:1.45; color:var(--ink); background:#fff; border:1px solid var(--line); border-radius:8px; padding:.5rem .7rem}
.note::placeholder{color:#a6a99f}

/* export bar */
.exportbar{position:sticky; bottom:1rem; z-index:6; margin-top:2.5rem; background:var(--ink); color:#fff; border-radius:12px; display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.85rem 1.1rem; box-shadow:0 8px 30px rgba(0,0,0,.22); flex-wrap:wrap}
.tally{font-size:.85rem; color:rgba(255,255,255,.78); font-variant-numeric:tabular-nums}
.ebtns{display:flex; gap:.5rem; flex-wrap:wrap}
.ebtn{font:inherit; font-size:.85rem; font-weight:600; cursor:pointer; border:0; border-radius:100px; padding:.55rem 1.05rem; background:#fff; color:var(--ink); transition:opacity .15s}
.ebtn--ghost{background:transparent; color:#fff; border:1px solid rgba(255,255,255,.4)}
.ebtn:hover{opacity:.85}

/* notes + footer */
.notes{margin-top:3rem; background:#1f211d; color:#e9eae5; border-radius:6px; padding:2.2rem 2rem}
.notes h2{font-family:"Newsreader",serif; font-weight:400; font-size:1.5rem; margin:0 0 1rem}
.notes-intro{color:#c7c9c1; margin:0 0 1.2rem}
.notes-list{display:flex; flex-direction:column; gap:.9rem; counter-reset:n}
.notes-list li{position:relative; padding-left:2.1rem; color:#d9dad3; font-size:.97rem}
.notes-list li::before{counter-increment:n; content:counter(n); position:absolute; left:0; top:0; width:1.5rem; height:1.5rem; border-radius:50%; background:#34372f; color:#e9eae5; font-size:.78rem; font-weight:700; display:flex; align-items:center; justify-content:center}
footer{margin-top:2.5rem; color:var(--muted); font-size:.85rem; border-top:1px solid var(--line); padding-top:1.4rem}

/* toast */
.toast{position:fixed; left:50%; bottom:6rem; transform:translateX(-50%) translateY(1rem); opacity:0; transition:opacity .2s,transform .2s; background:#111; color:#fff; padding:.65rem 1.1rem; border-radius:10px; font-size:.85rem; pointer-events:none; z-index:30}
.toast.show{opacity:1; transform:translateX(-50%)}

.is-hidden{display:none}
:focus-visible{outline:2px solid var(--ink); outline-offset:3px; border-radius:3px}
@media (max-width:560px){
  body{font-size:16px}
  .conv{padding:1.5rem 1.3rem}
  .stats{gap:1.4rem}
}
@media (prefers-reduced-motion:reduce){ html{scroll-behavior:auto} *{transition:none !important} }
"""

JS = r"""
(function(){
  var KEY='hd-curation-2026-06-27';
  var state={};
  try{ state=JSON.parse(localStorage.getItem(KEY)||'{}'); }catch(e){ state={}; }
  var cards=[].slice.call(document.querySelectorAll('.conv'));

  // type filter
  var fbtns=[].slice.call(document.querySelectorAll('.f'));
  fbtns.forEach(function(b){
    b.addEventListener('click',function(){
      var f=b.dataset.filter;
      fbtns.forEach(function(x){var on=x===b;x.classList.toggle('is-active',on);x.setAttribute('aria-pressed',on);});
      cards.forEach(function(c){c.classList.toggle('is-hidden', f!=='all' && c.dataset.type!==f);});
    });
  });

  function save(){ try{ localStorage.setItem(KEY,JSON.stringify(state)); }catch(e){} }
  function tally(){
    var k=0,m=0,c=0;
    cards.forEach(function(card){var s=card.dataset.status; if(s==='cut')c++; else if(s==='maybe')m++; else k++;});
    document.getElementById('tally').textContent=k+' keep · '+m+' maybe · '+c+' cut';
  }

  cards.forEach(function(card){
    var id=card.id;
    var st=state[id]||(state[id]={status:'keep',note:'',dropped:{}});
    card.dataset.status=st.status||'keep';
    var segBtns=[].slice.call(card.querySelectorAll('.seg-btn'));
    segBtns.forEach(function(sb){
      var on=sb.dataset.status===card.dataset.status;
      sb.classList.toggle('is-on',on); sb.setAttribute('aria-checked',on);
      sb.addEventListener('click',function(){
        st.status=sb.dataset.status; card.dataset.status=st.status;
        segBtns.forEach(function(x){var o=x===sb;x.classList.toggle('is-on',o);x.setAttribute('aria-checked',o);});
        save(); tally();
      });
    });
    var note=card.querySelector('.note');
    note.value=st.note||'';
    note.addEventListener('input',function(){ st.note=note.value; save(); });
    [].slice.call(card.querySelectorAll('.fits input')).forEach(function(cb){
      var nm=cb.dataset.name;
      st.dropped=st.dropped||{};
      var dropped=!!st.dropped[nm];
      cb.checked=!dropped; cb.closest('li').classList.toggle('dropped',dropped);
      cb.addEventListener('change',function(){
        if(cb.checked){ delete st.dropped[nm]; } else { st.dropped[nm]=1; }
        cb.closest('li').classList.toggle('dropped',!cb.checked);
        save();
      });
    });
  });
  tally();

  function buildMd(){
    var groups={keep:[],maybe:[],cut:[]};
    cards.forEach(function(card){
      var st=state[card.id]||{status:'keep'};
      var kept=[],dropped=[];
      [].slice.call(card.querySelectorAll('.fits input')).forEach(function(cb){
        (cb.checked?kept:dropped).push(cb.dataset.name);
      });
      groups[st.status||'keep'].push({
        title:card.querySelector('.conv__title').textContent.trim(),
        type:card.dataset.type, kept:kept, dropped:dropped, note:(st.note||'').trim()
      });
    });
    var out='# Curation — Hybrid Dialogue conversations\n\n';
    function sec(label,items){
      if(!items.length) return '';
      var s='## '+label+'\n\n';
      items.forEach(function(it){
        s+='### '+it.title+'  ['+it.type+']\n';
        if(label!=='Cut'){
          s+='- People: '+(it.kept.join(', ')||'(none)')+'\n';
          if(it.dropped.length) s+='- Dropped: '+it.dropped.join(', ')+'\n';
        }
        if(it.note) s+='- Note: '+it.note+'\n';
        s+='\n';
      });
      return s;
    }
    return (out+sec('Keep',groups.keep)+sec('Maybe',groups.maybe)+sec('Cut',groups.cut)).trim()+'\n';
  }

  var toastEl=document.getElementById('toast'), tt;
  function toast(m){ toastEl.textContent=m; toastEl.classList.add('show'); clearTimeout(tt); tt=setTimeout(function(){toastEl.classList.remove('show');},1900); }
  function copy(text,msg){
    function fb(){ var ta=document.createElement('textarea'); ta.value=text; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select(); try{document.execCommand('copy');}catch(e){} document.body.removeChild(ta); }
    if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(text).then(function(){toast(msg);},function(){fb();toast(msg);}); }
    else { fb(); toast(msg); }
  }
  document.getElementById('copyMd').addEventListener('click',function(){ copy(buildMd(),'Curation copied as Markdown'); });
  document.getElementById('copyPrompt').addEventListener('click',function(){
    copy("Here's how I'd like to revise the conversation set for the inquiry — please update accordingly.\n\n"+buildMd(),'Copied as a prompt for Claude');
  });
})();
"""


def build(data, model, date_str):
    invs = data.get("invitations", [])
    filters_html, kinds = render_filters(invs)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Conversations to open the inquiry &middot; Hybrid Dialogue</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>""" + CSS + """</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <p class="kicker">Hybrid Dialogue &middot; draft for curation</p>
    <h1>Six conversations,<br>drawn from <em>sixteen voices</em></h1>
    <p class="lede">A starting set, generated from the survey. Each one is grounded in what people actually wrote &mdash; with who might join, and who's still missing. A draft: keep, cut, merge, and reassign freely.</p>
    <div class="stats">
      <div class="stat"><b>""" + str(len(invs)) + """</b><span>Conversations</span></div>
      <div class="stat"><b>16</b><span>Voices</span></div>
      <div class="stat"><b>""" + str(kinds) + """</b><span>Kinds</span></div>
    </div>
  </header>

  <nav class="filters" aria-label="Filter conversations by kind">
        """ + filters_html + """
  </nav>

  <p class="howto">Curate as you read: set each conversation to <strong>Keep / Maybe / Cut</strong>, uncheck anyone who doesn't fit, and jot notes. Then copy your decisions from the bar at the bottom. Your choices are saved in this browser.</p>

  <main class="feed">
""" + render_cards(invs) + """
  </main>

  <div class="exportbar">
    <span class="tally" id="tally"></span>
    <div class="ebtns">
      <button class="ebtn" id="copyMd">Copy curation as Markdown</button>
      <button class="ebtn ebtn--ghost" id="copyPrompt">Copy as prompt</button>
    </div>
  </div>

  <section class="notes" aria-label="Reading notes">
    <h2>Reading notes</h2>
    """ + render_notes(data.get("notes_for_curation", "")) + """
  </section>

  <footer>
    Generated from 16 survey responses with """ + e(model) + """ &middot; """ + e(date_str) + """.
    Claude read the responses and clustered them into a starting set; the choices are yours.
  </footer>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>""" + JS + """</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", help="invitations-*.json (defaults to newest in ./output)")
    ap.add_argument("--out", default=str(HERE / "output"))
    ap.add_argument("--model", default="claude-opus-4-8")
    args = ap.parse_args()

    inp = args.input
    if not inp:
        cands = sorted(glob.glob(str(HERE / "output" / "invitations-*.json")))
        if not cands:
            raise SystemExit("No invitations-*.json found; pass --input")
        inp = cands[-1]

    data = json.loads(pathlib.Path(inp).read_text(encoding="utf-8"))
    m = re.search(r"(\d{4}-\d{2}-\d{2})", pathlib.Path(inp).name)
    date_str = m.group(1) if m else datetime.date.today().isoformat()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"invitations-{date_str}.html"
    dest.write_text(build(data, args.model, date_str), encoding="utf-8")
    print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
