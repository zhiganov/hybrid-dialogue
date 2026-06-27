#!/usr/bin/env python3
"""
Render the invitation-generator JSON into a single, navigable, interactive HTML page.

Design: a naturalist's field catalogue (see DESIGN.md / PRODUCT.md) — warm paper,
sepia ink, specimen entries with classification tags and margin annotations. Built
to Thariq Shihipar's "HTML over Markdown" idea: a long brief doesn't get read or
acted on, so this is navigable and "ends with an export" — the convener curates
(keep / maybe / cut, drop people) and copies the decisions back out.

Reads the JSON that generate.py wrote; emits one self-contained HTML file (no build).

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
    "content":    {"label": "Content",    "color": "oklch(0.5 0.08 150)"},
    "tension":    {"label": "Tension",    "color": "oklch(0.52 0.13 38)"},
    "process":    {"label": "Process",    "color": "oklch(0.46 0.08 256)"},
    "relational": {"label": "Relational", "color": "oklch(0.6 0.1 75)"},
}

WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
         7: "Seven", 8: "Eight", 9: "Nine", 16: "Sixteen"}


def e(s: str) -> str:
    return html.escape(str(s), quote=True)


def word(n: int) -> str:
    return WORDS.get(n, str(n))


def render_entries(invs):
    out = []
    for i, inv in enumerate(invs, 1):
        t = inv.get("type", "content")
        meta = TYPES.get(t, TYPES["content"])
        voices = "".join(f"<li>{e(v)}</li>" for v in inv.get("grounded_in", []))
        fits = "".join(
            f'<li><label><input type="checkbox" class="pk" data-name="{e(p["name"])}" checked>'
            f'<span class="who"><span class="nm">{e(p["name"])}</span>'
            f'<span class="why">{e(p["why"])}</span></span></label></li>'
            for p in inv.get("recommended_participants", [])
        )
        absent = "".join(f"<li>{e(a)}</li>" for a in inv.get("archetypes_to_invite", []))
        out.append(f"""
      <article class="entry" data-type="{t}" data-status="keep" id="c{i}" style="--k:{meta['color']}">
        <div class="gutter">
          <span class="acc">{i:02d}</span>
          <span class="tag"><span class="swatch"></span>{meta['label']}</span>
          <div class="disp" role="radiogroup" aria-label="Decision for this conversation">
            <button class="stamp" data-status="keep" role="radio" aria-checked="true">Keep</button>
            <button class="stamp" data-status="maybe" role="radio" aria-checked="false">Maybe</button>
            <button class="stamp" data-status="cut" role="radio" aria-checked="false">Cut</button>
          </div>
        </div>
        <div class="body">
          <h2 class="title">{e(inv.get('title',''))}</h2>
          <p class="desc">{e(inv.get('framing',''))}</p>
          <section class="sub">
            <h3 class="sublabel">Collected from</h3>
            <ul class="annot">{voices}</ul>
          </section>
          <section class="sub">
            <h3 class="sublabel">Who fits <span class="hint">untick to drop</span></h3>
            <ul class="checklist">{fits}</ul>
          </section>
          <section class="sub">
            <h3 class="sublabel">Not yet in the collection</h3>
            <ul class="absent">{absent}</ul>
          </section>
          <textarea class="note" rows="1" placeholder="Margin note: merge with&hellip;, retitle, add someone&hellip;"></textarea>
        </div>
      </article>""")
    return "\n".join(out)


def render_browse(invs):
    present = [t for t in TYPES if any(v.get("type") == t for v in invs)]
    tags = [f'<button class="ftag is-on" data-filter="all" aria-pressed="true">'
            f'All <span class="ct">{len(invs)}</span></button>']
    for t in present:
        n = sum(1 for v in invs if v.get("type") == t)
        tags.append(
            f'<button class="ftag" data-filter="{t}" aria-pressed="false" style="--k:{TYPES[t]["color"]}">'
            f'<span class="swatch"></span>{TYPES[t]["label"]} <span class="ct">{n}</span></button>'
        )
    return "\n        ".join(tags), len(present)


def render_notes(notes: str) -> str:
    parts = re.split(r"\((\d+)\)\s*", notes.strip())
    intro = e(parts[0].strip())
    items = "".join(f"<li>{e(parts[j+1].strip())}</li>" for j in range(1, len(parts) - 1, 2))
    lst = f'<ol class="notelist">{items}</ol>' if items else ""
    return f'<p class="note-intro">{intro}</p>{lst}'


CSS = """
:root{
  --paper:oklch(0.925 0.018 80);
  --sheet:oklch(0.955 0.013 85);
  --ink:oklch(0.27 0.018 60);
  --ink-soft:oklch(0.44 0.02 62);
  --faint:oklch(0.58 0.016 68);
  --rule:oklch(0.82 0.02 75);
  --k:oklch(0.5 0.08 150);
  --maybe:oklch(0.62 0.1 75);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"Atkinson Hyperlegible",system-ui,sans-serif;
  font-size:17px; line-height:1.62; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:53rem; margin:0 auto; padding:0 clamp(1.1rem,4vw,2.5rem) 2rem}
::selection{background:oklch(0.85 0.06 80)}

/* masthead */
.masthead{padding:clamp(3rem,9vw,5.5rem) 0 1.6rem}
.kicker{font-size:.74rem; letter-spacing:.22em; text-transform:uppercase; color:var(--faint); margin:0 0 1.5rem; font-weight:700}
.masthead h1{
  font-family:"Bitter",Georgia,serif; font-weight:600; color:var(--ink);
  font-size:clamp(2.1rem,6vw,3.3rem); line-height:1.08; letter-spacing:-.005em; margin:0 0 1.1rem;
}
.lede{font-size:1.1rem; color:var(--ink-soft); max-width:38rem; margin:0 0 1.6rem}
.coll{font-size:.74rem; letter-spacing:.16em; text-transform:uppercase; color:var(--faint); font-weight:700;
  border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); padding:.8rem 0; margin:0}

/* browse-by-kind */
.browse{display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; margin:1.4rem 0 0}
.browse-label{font-size:.74rem; letter-spacing:.14em; text-transform:uppercase; color:var(--faint); font-weight:700; margin-right:.3rem}
.ftag{font:inherit; font-size:.82rem; font-weight:700; cursor:pointer; background:transparent; color:var(--ink-soft);
  border:1px solid var(--rule); border-radius:2px; padding:.3rem .6rem; display:inline-flex; align-items:center; gap:.4rem;
  transition:color .15s,border-color .15s,background .15s}
.ftag .swatch{width:.62rem; height:.62rem; background:var(--k); border-radius:1px; flex:0 0 auto}
.ftag .ct{color:var(--faint); font-variant-numeric:tabular-nums}
.ftag:hover{border-color:var(--ink-soft); color:var(--ink)}
.ftag.is-on{background:var(--ink); color:var(--paper); border-color:var(--ink)}
.ftag.is-on .ct{color:oklch(0.78 0.02 80)}
.ftag[data-filter="all"] .swatch{display:none}

/* catalogue */
.feed{margin-top:.5rem}
.entry{
  display:grid; grid-template-columns:8.5rem 1fr; gap:0 2.2rem;
  border-top:1px solid var(--rule); padding:2.2rem 0;
  transition:opacity .25s ease;
}
.entry[data-status="cut"]{opacity:.42}
.entry[data-status="cut"] .title{text-decoration:line-through; text-decoration-thickness:1px}

.gutter{display:flex; flex-direction:column; gap:.9rem; align-items:flex-start}
.acc{font-family:"Bitter",serif; font-weight:600; font-size:1.7rem; color:var(--faint); line-height:1; font-variant-numeric:tabular-nums}
.tag{display:inline-flex; align-items:center; gap:.45rem; font-size:.72rem; letter-spacing:.13em; text-transform:uppercase; font-weight:700; color:var(--ink)}
.tag .swatch{width:.66rem; height:.66rem; background:var(--k); border-radius:1px; flex:0 0 auto}
.disp{display:flex; flex-direction:column; gap:.3rem; align-items:stretch; width:100%}
.stamp{font:inherit; font-size:.76rem; font-weight:700; cursor:pointer; text-align:left;
  background:transparent; color:var(--ink-soft); border:1px solid var(--rule); border-radius:2px; padding:.28rem .5rem;
  transition:background .12s,color .12s,border-color .12s}
.stamp:hover{border-color:var(--ink-soft); color:var(--ink)}
.stamp.on[data-status="keep"]{background:var(--ink); color:var(--paper); border-color:var(--ink)}
.stamp.on[data-status="maybe"]{background:var(--maybe); color:oklch(0.28 0.04 70); border-color:var(--maybe)}
.stamp.on[data-status="cut"]{background:transparent; color:var(--ink); border-color:var(--ink-soft); text-decoration:line-through}

.body{min-width:0}
.title{font-family:"Bitter",Georgia,serif; font-weight:600; font-size:clamp(1.35rem,2.7vw,1.85rem); line-height:1.18; letter-spacing:-.005em; margin:.1rem 0 .9rem}
.desc{margin:0 0 1.5rem; color:var(--ink); max-width:60ch}
.sub{margin:1.2rem 0 0}
.sublabel{font-size:.7rem; letter-spacing:.15em; text-transform:uppercase; color:var(--faint); font-weight:700; margin:0 0 .6rem}
.sublabel .hint{text-transform:none; letter-spacing:0; font-weight:400; color:var(--faint); font-style:italic}
ul,ol{margin:0; padding:0; list-style:none}

.annot li{font-family:"Bitter",serif; font-style:italic; font-size:1rem; line-height:1.5; color:var(--ink-soft);
  padding-left:1.2em; text-indent:-1.2em; margin:0 0 .55rem; max-width:62ch}
.annot li::before{content:"\\2014\\00a0"; color:var(--faint); font-style:normal}

.checklist li{margin:0 0 .5rem}
.checklist label{display:flex; gap:.6rem; align-items:baseline; cursor:pointer}
.checklist input{margin:.25rem 0 0; width:1rem; height:1rem; accent-color:var(--k); flex:0 0 auto; cursor:pointer}
.checklist .nm{font-weight:700}
.checklist .why{color:var(--ink-soft)}
.checklist li.dropped .who{opacity:.4; text-decoration:line-through}

.absent li{color:var(--ink-soft); padding-left:1.2em; text-indent:-1.2em; margin:0 0 .45rem; max-width:60ch}
.absent li::before{content:"+\\00a0"; color:var(--k); font-weight:700}

.note{margin-top:1.3rem; width:100%; min-height:2.5rem; resize:vertical; font:inherit; font-size:.95rem;
  color:var(--ink); background:var(--sheet); border:1px solid var(--rule); border-radius:2px; padding:.55rem .7rem}
.note::placeholder{color:var(--faint); font-style:italic}

/* field-log footer (export) */
.fieldlog{position:sticky; bottom:0; z-index:6; margin:2.5rem -1rem 0; padding:.85rem 1rem;
  background:var(--paper); border-top:1px solid var(--ink-soft);
  display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap}
.tally{font-size:.85rem; color:var(--ink-soft); font-weight:700; letter-spacing:.04em; font-variant-numeric:tabular-nums}
.logbtns{display:flex; gap:.5rem; flex-wrap:wrap}
.logbtn{font:inherit; font-size:.84rem; font-weight:700; cursor:pointer; border-radius:2px; padding:.5rem .9rem;
  background:var(--ink); color:var(--paper); border:1px solid var(--ink); transition:opacity .15s}
.logbtn.ghost{background:transparent; color:var(--ink); border-color:var(--ink-soft)}
.logbtn:hover{opacity:.85}

/* editor's notes */
.editor{margin-top:3rem; background:var(--sheet); border:1px solid var(--rule); border-radius:3px; padding:clamp(1.4rem,4vw,2.2rem)}
.editor h2{font-family:"Bitter",serif; font-weight:600; font-size:1.4rem; margin:0 0 .9rem}
.note-intro{color:var(--ink-soft); margin:0 0 1.1rem}
.notelist{counter-reset:n; display:flex; flex-direction:column; gap:.8rem}
.notelist li{position:relative; padding-left:2rem; color:var(--ink-soft); font-size:.96rem; line-height:1.5}
.notelist li::before{counter-increment:n; content:counter(n,decimal-leading-zero);
  position:absolute; left:0; top:.05rem; font-family:"Bitter",serif; font-weight:600; font-size:.85rem; color:var(--faint); font-variant-numeric:tabular-nums}

footer{margin-top:2.5rem; color:var(--faint); font-size:.84rem; line-height:1.5; border-top:1px solid var(--rule); padding-top:1.4rem}

.is-hidden{display:none}
:focus-visible{outline:2px solid var(--ink); outline-offset:3px; border-radius:2px}
.toast{position:fixed; left:50%; bottom:5.5rem; transform:translateX(-50%) translateY(.8rem); opacity:0;
  transition:opacity .2s,transform .2s; background:var(--ink); color:var(--paper); padding:.6rem 1rem;
  border-radius:3px; font-size:.85rem; font-weight:700; pointer-events:none; z-index:30}
.toast.show{opacity:1; transform:translateX(-50%)}

@media (max-width:640px){
  body{font-size:16px}
  .entry{grid-template-columns:1fr; gap:1rem 0}
  .gutter{flex-direction:row; flex-wrap:wrap; align-items:center; gap:.7rem}
  .acc{font-size:1.3rem}
  .disp{flex-direction:row; width:auto; margin-left:auto}
}
@media (prefers-reduced-motion:reduce){ html{scroll-behavior:auto} *{transition:none !important} }
"""

JS = r"""
(function(){
  var KEY='hd-curation-2026-06-27';
  var state={};
  try{ state=JSON.parse(localStorage.getItem(KEY)||'{}'); }catch(e){ state={}; }
  var cards=[].slice.call(document.querySelectorAll('.entry'));

  var ftags=[].slice.call(document.querySelectorAll('.ftag'));
  ftags.forEach(function(b){
    b.addEventListener('click',function(){
      var f=b.dataset.filter;
      ftags.forEach(function(x){var on=x===b;x.classList.toggle('is-on',on);x.setAttribute('aria-pressed',on);});
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
    var stamps=[].slice.call(card.querySelectorAll('.stamp'));
    stamps.forEach(function(sb){
      var on=sb.dataset.status===card.dataset.status;
      sb.classList.toggle('on',on); sb.setAttribute('aria-checked',on);
      sb.addEventListener('click',function(){
        st.status=sb.dataset.status; card.dataset.status=st.status;
        stamps.forEach(function(x){var o=x===sb;x.classList.toggle('on',o);x.setAttribute('aria-checked',o);});
        save(); tally();
      });
    });
    var note=card.querySelector('.note');
    note.value=st.note||'';
    note.addEventListener('input',function(){ st.note=note.value; save(); });
    [].slice.call(card.querySelectorAll('.pk')).forEach(function(cb){
      var nm=cb.dataset.name; st.dropped=st.dropped||{};
      var dropped=!!st.dropped[nm];
      cb.checked=!dropped; cb.closest('li').classList.toggle('dropped',dropped);
      cb.addEventListener('change',function(){
        if(cb.checked){ delete st.dropped[nm]; } else { st.dropped[nm]=1; }
        cb.closest('li').classList.toggle('dropped',!cb.checked); save();
      });
    });
  });
  tally();

  function buildMd(){
    var g={keep:[],maybe:[],cut:[]};
    cards.forEach(function(card){
      var st=state[card.id]||{status:'keep'};
      var kept=[],dropped=[];
      [].slice.call(card.querySelectorAll('.pk')).forEach(function(cb){ (cb.checked?kept:dropped).push(cb.dataset.name); });
      g[st.status||'keep'].push({title:card.querySelector('.title').textContent.trim(), type:card.dataset.type,
        kept:kept, dropped:dropped, note:(st.note||'').trim()});
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
    return (out+sec('Keep',g.keep)+sec('Maybe',g.maybe)+sec('Cut',g.cut)).trim()+'\n';
  }

  var toastEl=document.getElementById('toast'), tt;
  function toast(m){ toastEl.textContent=m; toastEl.classList.add('show'); clearTimeout(tt); tt=setTimeout(function(){toastEl.classList.remove('show');},1900); }
  function copy(text,msg){
    function fb(){ var ta=document.createElement('textarea'); ta.value=text; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select(); try{document.execCommand('copy');}catch(e){} document.body.removeChild(ta); }
    if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(text).then(function(){toast(msg);},function(){fb();toast(msg);}); }
    else { fb(); toast(msg); }
  }
  document.getElementById('copyMd').addEventListener('click',function(){ copy(buildMd(),'Decisions copied as Markdown'); });
  document.getElementById('copyPrompt').addEventListener('click',function(){
    copy("Here's how I'd like to revise the conversation set for the inquiry — please update accordingly.\n\n"+buildMd(),'Copied as a prompt for Claude');
  });
})();
"""


def build(data, model, date_str):
    invs = data.get("invitations", [])
    browse_html, kinds = render_browse(invs)
    nice_date = ""
    try:
        nice_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%-d %B %Y")
    except ValueError:
        try:
            nice_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%#d %B %Y")
        except ValueError:
            nice_date = date_str
    coll = (f"{word(len(invs))} entries &middot; sixteen contributors &middot; "
            f"{word(kinds)} kinds &middot; {e(nice_date)}")
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Hybrid Dialogue &middot; a field catalogue of conversations</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bitter:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
<style>""" + CSS + """</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <p class="kicker">Hybrid Dialogue &middot; a field catalogue</p>
    <h1>Six conversations,<br>drawn from sixteen voices</h1>
    <p class="lede">A starting set, gathered from the survey. Each is grown from what people actually wrote, with who might join and who's not yet here. A draft: keep, set aside, or cut, and reassign freely.</p>
    <p class="coll">""" + coll + """</p>
    <div class="browse">
      <span class="browse-label">Browse by kind</span>
        """ + browse_html + """
    </div>
  </header>

  <main class="feed">
""" + render_entries(invs) + """
  </main>

  <div class="fieldlog">
    <span class="tally" id="tally"></span>
    <div class="logbtns">
      <button class="logbtn" id="copyMd">Copy decisions</button>
      <button class="logbtn ghost" id="copyPrompt">Copy as prompt</button>
    </div>
  </div>

  <section class="editor" aria-label="Editor's notes">
    <h2>From the field notes</h2>
    """ + render_notes(data.get("notes_for_curation", "")) + """
  </section>

  <footer>
    Gathered from sixteen survey responses with """ + e(model) + """ on """ + e(nice_date) + """.
    Claude read the responses and grouped them into a starting set; the choices are yours.
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
