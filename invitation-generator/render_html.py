#!/usr/bin/env python3
"""
Render the invitation-generator JSON into a single, navigable, interactive HTML page.

Design: a naturalist's field catalogue (see DESIGN.md / PRODUCT.md) — warm paper,
sepia ink, specimen entries with classification tags and margin annotations.

It's an artifact for the whole group, not just the convener. Following Thariq
Shihipar's "HTML over Markdown" idea (a long brief doesn't get read or acted on),
each reader marks the conversations that pull them and "ends with an export":
copies their own picks to share or sign up.

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
        people = "".join(
            f'<li><span class="nm">{e(p["name"])}</span> '
            f'<span class="why">{e(p["why"])}</span></li>'
            for p in inv.get("recommended_participants", [])
        )
        absent = "".join(f"<li>{e(a)}</li>" for a in inv.get("archetypes_to_invite", []))
        out.append(f"""
      <article class="entry" data-type="{t}" id="c{i}" style="--k:{meta['color']}">
        <div class="gutter">
          <span class="acc">{i:02d}</span>
          <span class="tag"><span class="swatch"></span>{meta['label']}</span>
          <button class="join" aria-pressed="false"><span class="jl">Add to my list</span></button>
        </div>
        <div class="body">
          <h2 class="title">{e(inv.get('title',''))}</h2>
          <p class="desc">{e(inv.get('framing',''))}</p>
          <section class="sub">
            <h3 class="sublabel">Collected from</h3>
            <ul class="annot">{voices}</ul>
          </section>
          <section class="sub">
            <h3 class="sublabel">Who might fit</h3>
            <ul class="people">{people}</ul>
          </section>
          <section class="sub">
            <h3 class="sublabel">Not yet in the collection</h3>
            <ul class="absent">{absent}</ul>
          </section>
          <textarea class="note" rows="1" placeholder="Add a note (optional): what you'd bring, a question, a thought"></textarea>
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
    tags.append('<button class="ftag ftag-mine" data-filter="mine" aria-pressed="false">'
                'My list <span class="ct" id="mineCt">0</span></button>')
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
.masthead h1{font-family:"Bitter",Georgia,serif; font-weight:600; color:var(--ink);
  font-size:clamp(2.1rem,6vw,3.3rem); line-height:1.08; letter-spacing:-.005em; margin:0 0 1.1rem}
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
.ftag-mine{margin-left:.4rem}

/* catalogue */
.feed{margin-top:.5rem}
.entry{display:grid; grid-template-columns:8.5rem 1fr; gap:0 2.2rem;
  border-top:1px solid var(--rule); padding:2.2rem 0; transition:background .2s ease}
.entry[data-chosen]{background:linear-gradient(90deg, oklch(0.95 0.02 80) 0%, transparent 60%)}

.gutter{display:flex; flex-direction:column; gap:.9rem; align-items:flex-start}
.acc{font-family:"Bitter",serif; font-weight:600; font-size:1.7rem; color:var(--faint); line-height:1;
  font-variant-numeric:tabular-nums; transition:color .15s}
.entry[data-chosen] .acc{color:var(--ink)}
.tag{display:inline-flex; align-items:center; gap:.45rem; font-size:.72rem; letter-spacing:.13em; text-transform:uppercase; font-weight:700; color:var(--ink)}
.tag .swatch{width:.66rem; height:.66rem; background:var(--k); border-radius:1px; flex:0 0 auto}
.join{font:inherit; font-size:.78rem; font-weight:700; cursor:pointer; text-align:left; width:100%;
  background:transparent; color:var(--ink); border:1px solid var(--ink-soft); border-radius:2px; padding:.4rem .6rem;
  display:inline-flex; align-items:center; gap:.4rem; transition:background .12s,color .12s,border-color .12s}
.join::before{content:"+"; font-weight:700; opacity:.7}
.join:hover{border-color:var(--ink)}
.join.on{background:var(--ink); color:var(--paper); border-color:var(--ink)}
.join.on::before{content:"\\2713"; opacity:1}

.body{min-width:0}
.title{font-family:"Bitter",Georgia,serif; font-weight:600; font-size:clamp(1.35rem,2.7vw,1.85rem); line-height:1.18; letter-spacing:-.005em; margin:.1rem 0 .9rem}
.desc{margin:0 0 1.5rem; color:var(--ink); max-width:60ch}
.sub{margin:1.2rem 0 0}
.sublabel{font-size:.7rem; letter-spacing:.15em; text-transform:uppercase; color:var(--faint); font-weight:700; margin:0 0 .6rem}
ul,ol{margin:0; padding:0; list-style:none}

.annot li{font-family:"Bitter",serif; font-style:italic; font-size:1rem; line-height:1.5; color:var(--ink-soft);
  padding-left:1.2em; text-indent:-1.2em; margin:0 0 .55rem; max-width:62ch}
.annot li::before{content:"\\2014\\00a0"; color:var(--faint); font-style:normal}

.people li{margin:0 0 .5rem; max-width:60ch}
.people .nm{font-weight:700}
.people .why{color:var(--ink-soft)}

.absent li{color:var(--ink-soft); padding-left:1.2em; text-indent:-1.2em; margin:0 0 .45rem; max-width:60ch}
.absent li::before{content:"+\\00a0"; color:var(--k); font-weight:700}

.note{display:none; margin-top:1.3rem; width:100%; min-height:2.5rem; resize:vertical; font:inherit; font-size:.95rem;
  color:var(--ink); background:var(--sheet); border:1px solid var(--rule); border-radius:2px; padding:.55rem .7rem}
.entry[data-chosen] .note{display:block}
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
.editor .sublabel{margin-bottom:1.1rem}
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
  .entry[data-chosen]{background:linear-gradient(180deg, oklch(0.95 0.02 80) 0%, transparent 30%)}
  .gutter{flex-direction:row; flex-wrap:wrap; align-items:center; gap:.7rem}
  .acc{font-size:1.3rem}
  .join{width:auto; margin-left:auto}
}
@media (prefers-reduced-motion:reduce){ html{scroll-behavior:auto} *{transition:none !important} }
"""

JS = r"""
(function(){
  var KEY='hd-picks-2026-06-27';
  var state={};
  try{ state=JSON.parse(localStorage.getItem(KEY)||'{}'); }catch(e){ state={}; }
  var cards=[].slice.call(document.querySelectorAll('.entry'));

  function save(){ try{ localStorage.setItem(KEY,JSON.stringify(state)); }catch(e){} }
  function chosenCount(){ return cards.filter(function(c){return c.dataset.chosen;}).length; }
  function refresh(){
    var n=chosenCount();
    document.getElementById('tally').textContent = n ? (n+' of '+cards.length+' on your list') : 'Nothing on your list yet';
    document.getElementById('mineCt').textContent = n;
    var mine=document.querySelector('.ftag-mine');
    if(mine.classList.contains('is-on')) applyFilter('mine');
  }
  function applyFilter(f){
    cards.forEach(function(c){
      var show = f==='all' || (f==='mine' ? !!c.dataset.chosen : c.dataset.type===f);
      c.classList.toggle('is-hidden', !show);
    });
  }

  var ftags=[].slice.call(document.querySelectorAll('.ftag'));
  ftags.forEach(function(b){
    b.addEventListener('click',function(){
      ftags.forEach(function(x){var on=x===b;x.classList.toggle('is-on',on);x.setAttribute('aria-pressed',on);});
      applyFilter(b.dataset.filter);
    });
  });

  cards.forEach(function(card){
    var id=card.id;
    var st=state[id]||(state[id]={chosen:false,note:''});
    var join=card.querySelector('.join');
    var label=join.querySelector('.jl');
    function paint(){
      if(st.chosen){ card.dataset.chosen='1'; join.classList.add('on'); join.setAttribute('aria-pressed','true'); label.textContent='On my list'; }
      else { delete card.dataset.chosen; join.classList.remove('on'); join.setAttribute('aria-pressed','false'); label.textContent='Add to my list'; }
    }
    paint();
    join.addEventListener('click',function(){ st.chosen=!st.chosen; paint(); save(); refresh(); });
    var note=card.querySelector('.note');
    note.value=st.note||'';
    note.addEventListener('input',function(){ st.note=note.value; save(); });
  });
  refresh();

  function picks(){
    return cards.filter(function(c){return c.dataset.chosen;}).map(function(c){
      return { title:c.querySelector('.title').textContent.trim(), type:c.dataset.type, note:(state[c.id].note||'').trim() };
    });
  }
  function asMarkdown(p){
    var s='# My conversations — Hybrid Dialogue\n\n';
    p.forEach(function(it){ s+='- **'+it.title+'**  ['+it.type+']'+(it.note?'  — '+it.note:'')+'\n'; });
    return s;
  }
  function asMessage(p){
    var s="I'd like to join "+p.length+" of the conversations:\n";
    p.forEach(function(it,i){ s+=(i+1)+'. '+it.title+(it.note?' ('+it.note+')':'')+'\n'; });
    return s.trim();
  }

  var toastEl=document.getElementById('toast'), tt;
  function toast(m){ toastEl.textContent=m; toastEl.classList.add('show'); clearTimeout(tt); tt=setTimeout(function(){toastEl.classList.remove('show');},1900); }
  function copy(text,msg){
    function fb(){ var ta=document.createElement('textarea'); ta.value=text; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select(); try{document.execCommand('copy');}catch(e){} document.body.removeChild(ta); }
    if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(text).then(function(){toast(msg);},function(){fb();toast(msg);}); }
    else { fb(); toast(msg); }
  }
  document.getElementById('copyList').addEventListener('click',function(){
    var p=picks(); if(!p.length){ toast('Add a conversation to your list first'); return; }
    copy(asMarkdown(p),'Your list copied');
  });
  document.getElementById('copyMsg').addEventListener('click',function(){
    var p=picks(); if(!p.length){ toast('Add a conversation to your list first'); return; }
    copy(asMessage(p),'Copied as a message to share');
  });
})();
"""


def build(data, model, date_str):
    invs = data.get("invitations", [])
    browse_html, kinds = render_browse(invs)
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
    <p class="lede">A starting set, gathered from the survey. Each is grown from what people actually wrote, with who might join and who's not yet here. Mark the ones that pull you, add a note if you like, and copy your list to share.</p>
    <p class="coll">""" + coll + """</p>
    <div class="browse">
      <span class="browse-label">Browse</span>
        """ + browse_html + """
    </div>
  </header>

  <main class="feed">
""" + render_entries(invs) + """
  </main>

  <div class="fieldlog">
    <span class="tally" id="tally"></span>
    <div class="logbtns">
      <button class="logbtn" id="copyList">Copy my list</button>
      <button class="logbtn ghost" id="copyMsg">Copy as message</button>
    </div>
  </div>

  <section class="editor" aria-label="Notes on how this set was made">
    <h2>From the field notes</h2>
    <p class="sublabel">How this set was put together</p>
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
