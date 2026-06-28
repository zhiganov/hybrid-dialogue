#!/usr/bin/env python3
"""
Render the invitation-generator JSON into a single, navigable HTML page.

Design: a printed programme of conversations (see DESIGN.md / PRODUCT.md in
../node-room for the brand world). Warm paper and ink, one clay accent, confident
index numbers, real participant voices as the texture. Calm, legible, human;
deliberately out of the saturated "AI editorial" template.

Since node-room shipped, each conversation has a live room you enter via its
"join this conversation" link, so this page is a *lobby/index*, not a
curate-and-export catalogue. Each entry shows its framing and a join link, with
the supporting detail (voices, who fits, who is not yet here) folded into a
collapsed accordion to keep the page short.

Reads the JSON that generate.py wrote; emits one self-contained HTML file (no build).

Usage:
  python render_html.py --input output/invitations-2026-06-27.json \
      --rooms output/rooms-2026-06-27.json
"""
import argparse
import datetime
import glob
import html
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent

# The four conversation kinds. The WORD carries the meaning; there is no
# per-kind colour (one accent only), which is both calmer and less templated.
TYPES = {
    "content":    {"label": "Content"},
    "tension":    {"label": "Tension"},
    "process":    {"label": "Process"},
    "relational": {"label": "Relational"},
}

WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
         7: "Seven", 8: "Eight", 9: "Nine", 16: "Sixteen"}


def e(s: str) -> str:
    """Escape for HTML (attributes and URLs)."""
    return html.escape(str(s), quote=True)


def nd(s: str) -> str:
    """Deterministically strip em/en dashes from display copy.

    Em dashes are a hard no for this user's public-facing surfaces (and a classic
    AI tell). Replace em/en dashes with a comma; never touch hyphen-minus, so
    hyphenated words ('follow-the-sun', 'X-Matrix') are left alone.
    """
    s = re.sub(r"\s*[—–]\s*", ", ", str(s))
    s = re.sub(r",\s*,", ",", s)
    return s


def txt(s: str) -> str:
    """Normalize then escape: use for all human-readable copy."""
    return e(nd(s))


def word(n: int) -> str:
    return WORDS.get(n, str(n))


def kind_label(t: str) -> str:
    return TYPES.get(t, TYPES["content"])["label"]


def render_contents(invs):
    rows = []
    for i, inv in enumerate(invs, 1):
        k = kind_label(inv.get("type", "content")).lower()
        rows.append(
            f'<a class="toc-row" href="#c{i}">'
            f'<span class="toc-num">{i:02d}</span>'
            f'<span class="toc-title">{txt(inv.get("title", ""))}</span>'
            f'<span class="toc-kind">{e(k)}</span>'
            f'</a>'
        )
    return "\n        ".join(rows)


def render_entries(invs, room_urls):
    out = []
    for i, inv in enumerate(invs, 1):
        t = inv.get("type", "content")
        k = kind_label(t).lower()

        quotes = []
        for g in inv.get("grounded_in", []):
            g = str(g)
            who, body = (g.split(": ", 1) if ": " in g else ("", g))
            who_html = f'<span class="who">{txt(who)}</span>' if who.strip() else ""
            quotes.append(
                f'<p class="quote"><span class="q">{txt(body)}</span>{who_html}</p>'
            )
        quotes_html = "".join(quotes)

        people = "".join(
            f'<p class="person"><span class="nm">{txt(p.get("name", ""))}</span> '
            f'<span class="why">{txt(p.get("why", ""))}</span></p>'
            for p in inv.get("recommended_participants", [])
        )
        absent = "".join(
            f'<p class="arow">{txt(a)}</p>' for a in inv.get("archetypes_to_invite", [])
        )

        room_url = room_urls.get(inv.get("title", ""))
        actions = (
            f'<div class="actions"><a class="btn btn--primary" href="{e(room_url)}" target="_blank" rel="noopener">'
            f'join this conversation <span class="arr" aria-hidden="true">&rarr;</span></a></div>'
            if room_url else ""
        )

        out.append(f"""
      <article class="entry" data-type="{t}" id="c{i}">
        <p class="kind">{e(k)}</p>
        <h2 class="title">{txt(inv.get('title', ''))}</h2>
        <p class="framing">{txt(inv.get('framing', ''))}</p>
        <details class="more">
          <summary>Where this came from, and who might fit</summary>
          <div class="more-body">
            <section class="section">
              <h3 class="section-label">Collected from</h3>
              <div class="quotes">{quotes_html}</div>
            </section>
            <section class="section">
              <h3 class="section-label">Who might fit</h3>
              <div class="people">{people}</div>
            </section>
            <section class="section">
              <h3 class="section-label">Not yet here</h3>
              <div class="absent">{absent}</div>
            </section>
          </div>
        </details>
        {actions}
      </article>""")
    return "\n".join(out)


def render_filter(invs):
    present = [t for t in TYPES if any(v.get("type") == t for v in invs)]
    out = [f'<button class="ftag is-on" type="button" data-filter="all" aria-pressed="true">'
           f'All <span class="ct">{len(invs)}</span></button>']
    for t in present:
        n = sum(1 for v in invs if v.get("type") == t)
        out.append(
            f'<button class="ftag" type="button" data-filter="{t}" aria-pressed="false">'
            f'{kind_label(t)} <span class="ct">{n}</span></button>'
        )
    return "\n        ".join(out), len(present)


def render_notes(notes: str) -> str:
    parts = re.split(r"\((\d+)\)\s*", notes.strip())
    intro = txt(parts[0].strip())
    items = "".join(f"<li>{txt(parts[j + 1].strip())}</li>" for j in range(1, len(parts) - 1, 2))
    lst = f'<ol class="notelist">{items}</ol>' if items else ""
    return f'<p class="lead">{intro}</p>{lst}'


CSS = """
:root{
  --paper:        oklch(0.945 0.016 83);
  --raised:       oklch(0.915 0.020 80);
  --ink:          oklch(0.265 0.015 58);
  --ink-soft:     oklch(0.435 0.016 58);
  --faint:        oklch(0.505 0.016 64);
  --hairline:     oklch(0.795 0.020 76);
  --hairline-soft:oklch(0.865 0.016 80);
  --clay:         oklch(0.535 0.130 45);
  --clay-deep:    oklch(0.485 0.130 44);
  --clay-ink:     oklch(0.455 0.125 43);
  --clay-tint:    oklch(0.930 0.032 55);
  --on-clay:      oklch(0.975 0.012 83);

  --measure:62ch;
  --serif:"Bitter",Georgia,"Times New Roman",serif;
  --sans:"Atkinson Hyperlegible",system-ui,-apple-system,sans-serif;
}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth; -webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:var(--sans); font-size:1.0625rem; line-height:1.62;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
  overflow-wrap:break-word;
}
::selection{background:var(--clay-tint)}
:focus-visible{outline:2px solid var(--clay); outline-offset:3px; border-radius:4px}
.is-hidden{display:none !important}

.page{max-width:44rem; margin-inline:auto; padding-inline:clamp(1.15rem,5vw,2.5rem); padding-bottom:4rem}

/* masthead */
.masthead{padding-top:clamp(2.75rem,9vw,5rem); padding-bottom:.5rem}
.kicker{font-size:.95rem; font-weight:700; color:var(--clay-ink); margin:0 0 1.1rem}
.masthead h1{font-family:var(--serif); font-weight:600; color:var(--ink);
  font-size:clamp(2.05rem,7vw,3.6rem); line-height:1.06; letter-spacing:-.01em;
  margin:0 0 1rem; text-wrap:balance}
.lede{font-size:1.2rem; line-height:1.5; color:var(--ink-soft); max-width:34rem; margin:0 0 1.4rem; text-wrap:pretty}
.livelinks{display:flex; flex-wrap:wrap; gap:.6rem; margin:.5rem 0 0}
.sep{color:var(--faint); margin:0 .55rem}
/* contents / programme front matter */
.contents{margin:2.4rem 0 0; padding-top:1.6rem; border-top:1px solid var(--hairline)}
.contents h2{font-family:var(--serif); font-weight:600; font-size:1.2rem; margin:0 0 .4rem}
.toc{display:flex; flex-direction:column}
.toc-row{display:grid; grid-template-columns:2.3rem minmax(0,1fr) auto; gap:.15rem .85rem; align-items:baseline;
  text-decoration:none; color:var(--ink); padding:.62rem 0; border-top:1px solid var(--hairline-soft)}
.toc-row:first-child{border-top:0}
.toc-num{font-family:var(--serif); font-weight:600; color:var(--faint); font-variant-numeric:tabular-nums}
.toc-title{min-width:0; line-height:1.35}
.toc-row:hover .toc-title,.toc-row:focus-visible .toc-title{color:var(--clay-ink)}
.toc-kind{color:var(--faint); font-size:.85rem; white-space:nowrap}

/* filter strip (browse by kind) */
.filter{display:flex; flex-wrap:wrap; align-items:center; gap:.5rem; margin:2.6rem 0 0}
.filter-label{font-size:.85rem; color:var(--faint); font-weight:700; margin-right:.25rem}
.ftag{font:inherit; font-size:.95rem; font-weight:700; cursor:pointer; background:transparent; color:var(--ink-soft);
  border:1px solid var(--hairline); border-radius:7px; padding:.4rem .8rem; min-height:40px;
  transition:color .15s,border-color .15s,background .15s}
.ftag:hover{border-color:var(--ink-soft); color:var(--ink)}
.ftag.is-on{background:var(--clay); color:var(--on-clay); border-color:var(--clay)}
.ftag .ct{opacity:.72; font-variant-numeric:tabular-nums}

/* feed */
.feed{margin-top:1rem}
.entry{padding:clamp(2.1rem,5.5vw,3.2rem) 0; border-top:1px solid var(--hairline)}
.kind{font-size:.85rem; font-weight:700; color:var(--clay-ink); margin:0 0 .5rem}
.title{font-family:var(--serif); font-weight:600; color:var(--ink);
  font-size:clamp(1.5rem,3.8vw,2.15rem); line-height:1.16; letter-spacing:-.005em;
  margin:0 0 1rem; text-wrap:balance; max-width:26ch}
.framing{margin:0 0 .5rem; color:var(--ink); max-width:var(--measure)}

.section{margin:1.6rem 0 0}
.section-label{font-size:.85rem; font-weight:700; color:var(--clay-ink); margin:0 0 .75rem}

.quotes{display:flex; flex-direction:column; gap:1.05rem; max-width:var(--measure)}
.quote{margin:0}
.quote .q{font-family:var(--serif); font-style:italic; font-size:1.0625rem; line-height:1.5; color:var(--ink)}
.quote .who{display:block; margin-top:.3rem; font-size:.85rem; font-weight:700; color:var(--clay-ink)}

.people{display:flex; flex-direction:column; gap:.7rem; max-width:var(--measure)}
.person{margin:0}
.person .nm{font-weight:700; color:var(--ink)}
.person .why{color:var(--ink-soft)}

.absent{display:flex; flex-direction:column; gap:.5rem; max-width:var(--measure)}
.arow{margin:0; padding-left:1.4em; text-indent:-1.4em; color:var(--ink-soft)}
.arow::before{content:"+"; color:var(--clay); font-weight:700; margin-right:.55em}

/* detail accordion (native <details>) */
.more{margin:1.3rem 0 0; border-top:1px solid var(--hairline-soft)}
.more>summary{list-style:none; cursor:pointer; display:flex; align-items:center; gap:.55rem;
  padding:.9rem 0; font-weight:700; font-size:.95rem; color:var(--clay-ink); min-height:44px}
.more>summary::-webkit-details-marker{display:none}
.more>summary::before{content:"+"; color:var(--clay); font-weight:700; font-size:1.15em; line-height:1; width:1em; text-align:center}
.more[open]>summary::before{content:"\\2212"}
.more>summary:hover{color:var(--clay)}
.more-body{padding:.1rem 0 .5rem}
.more-body .section:first-child{margin-top:.4rem}

/* buttons */
.btn{font:inherit; font-size:1.0625rem; font-weight:700; cursor:pointer; text-decoration:none;
  display:inline-flex; align-items:center; justify-content:center; gap:.45rem;
  border-radius:8px; padding:.7rem 1.15rem; min-height:44px; border:1px solid transparent;
  transition:background .15s,border-color .15s,color .15s}
.btn .arr{transition:transform .2s ease}
.btn:hover .arr,.btn:focus-visible .arr{transform:translateX(3px)}
.btn--primary{background:var(--clay); color:var(--on-clay); border-color:var(--clay)}
.btn--primary:hover,.btn--primary:focus-visible{background:var(--clay-deep); border-color:var(--clay-deep); color:var(--on-clay)}
.btn--quiet{background:transparent; color:var(--clay-ink); border-color:var(--hairline)}
.btn--quiet:hover,.btn--quiet:focus-visible{border-color:var(--clay-ink); color:var(--clay)}
.btn--sm{font-size:.95rem; padding:.55rem .9rem; min-height:40px}

/* per-entry action */
.actions{margin:1.4rem 0 0}

/* how this set was made */
.notes{margin-top:3.6rem; background:var(--raised); border:1px solid var(--hairline-soft);
  border-radius:12px; padding:clamp(1.4rem,4vw,2.3rem)}
.notes h2{font-family:var(--serif); font-weight:600; font-size:1.4rem; margin:0 0 .9rem}
.notes .lead{color:var(--ink-soft); margin:0 0 1.3rem; max-width:var(--measure)}
.notelist{counter-reset:n; display:flex; flex-direction:column; gap:.95rem; margin:0; padding:0; list-style:none}
.notelist li{position:relative; padding-left:2.3rem; color:var(--ink-soft); line-height:1.55; max-width:var(--measure)}
.notelist li::before{counter-increment:n; content:counter(n,decimal-leading-zero);
  position:absolute; left:0; top:.05rem; font-family:var(--serif); font-weight:600; color:var(--clay);
  font-variant-numeric:tabular-nums}

.colophon{margin-top:3rem; color:var(--faint); font-size:.85rem; line-height:1.55;
  border-top:1px solid var(--hairline-soft); padding-top:1.4rem; max-width:var(--measure)}

@media (max-width:520px){
  .toc-row{grid-template-columns:2rem minmax(0,1fr)}
  .toc-kind{grid-column:2; margin-top:.1rem}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *{transition:none !important; animation:none !important}
}
"""

JS = r"""
(function(){
  var ftags=[].slice.call(document.querySelectorAll('.ftag'));
  var cards=[].slice.call(document.querySelectorAll('.entry'));
  ftags.forEach(function(b){
    b.addEventListener('click',function(){
      ftags.forEach(function(x){var on=x===b; x.classList.toggle('is-on',on); x.setAttribute('aria-pressed',on);});
      var f=b.dataset.filter;
      cards.forEach(function(c){ c.classList.toggle('is-hidden', !(f==='all'||c.dataset.type===f)); });
    });
  });
})();
"""


def build(data, model, date_str, room_urls=None, base=""):
    room_urls = room_urls or {}
    invs = data.get("invitations", [])
    filter_html, _ = render_filter(invs)
    try:
        nice_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%-d %B %Y")
    except ValueError:
        try:
            nice_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%#d %B %Y")
        except ValueError:
            nice_date = date_str
    live_links = (
        f'<div class="livelinks">'
        f'<a class="btn btn--quiet btn--sm" href="{e(base)}/" target="_blank" rel="noopener">'
        f'See all live conversations <span class="arr" aria-hidden="true">&rarr;</span></a>'
        f'<a class="btn btn--quiet btn--sm" href="{e(base)}/create" target="_blank" rel="noopener">'
        f'Propose another conversation <span class="arr" aria-hidden="true">&rarr;</span></a>'
        f'</div>'
    ) if base else ""
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Hybrid Dialogue &middot; six conversations</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bitter:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
<style>""" + CSS + """</style>
</head>
<body>
<div class="page">
  <header class="masthead">
    <p class="kicker">Hybrid Dialogue &middot; a programme of conversations</p>
    <h1>Six conversations, drawn from sixteen voices</h1>
    <p class="lede">A starting set, gathered from the survey. Each one grew from what people actually wrote. Read the framing, open the detail if you want it, and join the ones that pull you.</p>
    """ + live_links + """
  </header>

  <nav class="contents" aria-label="Contents">
    <h2>Contents</h2>
    <div class="toc">
        """ + render_contents(invs) + """
    </div>
  </nav>

  <div class="filter" role="group" aria-label="Filter conversations by kind">
    <span class="filter-label">Show</span>
        """ + filter_html + """
  </div>

  <main class="feed">
""" + render_entries(invs, room_urls) + """
  </main>

  <section class="notes" aria-label="How this set was made">
    <h2>How this set was made</h2>
    """ + render_notes(data.get("notes_for_curation", "")) + """
  </section>

  <footer class="colophon">
    Gathered from sixteen survey responses with """ + e(model) + """ on """ + e(nice_date) + """.
    Claude read the responses and grouped them into a starting set; the choices are yours.
  </footer>
</div>
<script>""" + JS + """</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", help="invitations-*.json (defaults to newest in ./output)")
    ap.add_argument("--out", default=str(HERE / "output"))
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--rooms", help="rooms-*.json from create_rooms.py (optional)")
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

    room_urls, base = {}, ""
    if args.rooms:
        rm = json.loads(pathlib.Path(args.rooms).read_text(encoding="utf-8"))
        base = rm.get("base_url", "")
        room_urls = {v["title"]: v["room_url"] for v in rm.get("rooms", {}).values()}

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"invitations-{date_str}.html"
    dest.write_text(build(data, args.model, date_str, room_urls, base), encoding="utf-8")
    print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
