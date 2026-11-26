"""Build the BSD-live website from data/ into site/dist/.

Same page structure as pequalnp.com: header with grouped navigation and a live
status strip; a home page with hero, verdict, counters, search, legend, the
frontier and the graveyard; plus Map, News, Programs, Papers, Letters, Live,
Feed, Contributors, Sponsors, About, How it works, Prize and Follow pages.

Usage:   python3 scripts/build_site.py
Preview: python3 -m http.server 8000 -d site/dist   then open http://localhost:8000
"""
import datetime, html, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "site" / "dist"

# ---- Settings: change these to match your project ------------------------
REPO = "https://github.com/DavidTsitsiashvili/birch-and-swinnerton"
SITE = "BSD ?"
TAGLINE = "A team of AI agents attacking the Birch and Swinnerton-Dyer conjecture, live."
FOUNDERS = "David Tsitsiashvili"
# ---------------------------------------------------------------------------

SYM = {"checked": "✓", "conjecture": "?", "in_progress": "⟳", "refuted": "✗", "dead": "†"}
LABEL = {"checked": "checked a result", "conjecture": "conjecture (unchecked)",
         "in_progress": "agent at work", "refuted": "refuted", "dead": "ruled dead"}
COLOR = {"checked": "#1a7f37", "conjecture": "#6e7781", "in_progress": "#0969da",
         "refuted": "#cf222e", "dead": "#8250df"}

NAV = [
    (None, [("/#map", "Map"), ("/news/", "News")]),
    ("Research", [("/programs/", "Programs"), ("/curves/", "Curves"), ("/papers/", "Papers"),
                  ("/papers/how/", "How papers are written"), ("/letters/", "Letters"),
                  ("/graveyard/", "Graveyard")]),
    ("Live", [("/live/", "Live"), ("/feed/", "Feed")]),
    ("People", [("/contributors/", "Contributors"), ("/join.txt", "Connect your own agent"),
                ("/sponsors/", "Sponsors")]),
    ("About", [("/about/", "What this is"), ("/how/", "How it works"),
               ("/prize/", "Prize money"), ("/follow/", "Follow")]),
]

CSS = """
:root{--fg:#1f2328;--bg:#fff;--muted:#6e7781;--line:#d0d7de;--soft:#f6f8fa;--link:#0969da}
@media(prefers-color-scheme:dark){:root{--fg:#e6edf3;--bg:#0d1117;--muted:#8b949e;
--line:#30363d;--soft:#161b22;--link:#58a6ff}}
*{box-sizing:border-box}body{margin:0;color:var(--fg);background:var(--bg);
font:16px/1.6 Georgia,"Times New Roman",serif}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
.skip{position:absolute;left:-999px}.skip:focus{left:10px;top:10px}
header{border-bottom:1px solid var(--line)}
.top{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 0 8px}
.logo{font-size:1.5rem;font-weight:bold;color:var(--fg)}.logo small{display:block;font-size:.8rem;
font-weight:normal;color:var(--muted)}
.btn{display:inline-block;border:1px solid var(--fg);border-radius:999px;padding:6px 16px;
font:600 .9rem system-ui,sans-serif;color:var(--fg)}.btn.solid{background:var(--fg);color:var(--bg)}
nav{display:flex;flex-wrap:wrap;gap:4px 18px;padding:6px 0 10px;font:.9rem system-ui,sans-serif}
nav .grp{position:relative}nav .grp>span{color:var(--muted);cursor:default}
nav .grp .menu{display:none;position:absolute;z-index:9;top:100%;left:0;min-width:210px;
background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 0}
nav .grp:hover .menu,nav .grp:focus-within .menu{display:block}
nav .menu a{display:block;padding:4px 14px}
.strip{display:flex;flex-wrap:wrap;gap:16px;padding:8px 0 12px;font:.85rem system-ui,sans-serif;
color:var(--muted)}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;
margin-right:6px;background:#8b949e}.dot.on{background:#1a7f37;box-shadow:0 0 6px #1a7f37}
code.join{background:var(--soft);padding:2px 6px;border-radius:4px}
h1{font-size:2.6rem;line-height:1.15;margin:40px 0 8px}h2{margin-top:44px}
.verdict{font-size:1.2rem}.sub{color:var(--muted);font-size:1.1rem}
.row{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0}
.stat{font:.95rem system-ui,sans-serif}.stat b{font-size:1.4rem;margin-right:6px}
.label{font:600 .75rem system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;
color:var(--muted)}
.search{width:100%;padding:10px 14px;border:1px solid var(--line);border-radius:8px;
font:1rem system-ui,sans-serif;background:var(--bg);color:var(--fg)}
#results div{padding:6px 0;border-bottom:1px solid var(--line)}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font:.85rem system-ui,sans-serif}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.card{border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.card h3{margin:0 0 4px}.item{padding:8px 0;border-bottom:1px solid var(--line)}
.item:last-child{border:0}.sym{font-weight:bold;margin-right:6px}
.meta{font:.8rem system-ui,sans-serif;color:var(--muted)}
table{border-collapse:collapse;width:100%;font:.88rem system-ui,sans-serif}
td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.msg{border-left:3px solid;padding:6px 12px;margin:10px 0}.planner{border-color:#8250df}
.agent{border-color:#0969da}.checker{border-color:#9a6700}.ok{border-color:#1a7f37}
pre{white-space:pre-wrap;font-size:.8rem;margin:4px 0;background:var(--soft);padding:8px;
border-radius:6px}details{border:1px solid var(--line);border-radius:8px;padding:8px 14px;
margin:12px 0}summary{cursor:pointer}.cta{text-align:center;padding:40px 0}
footer{border-top:1px solid var(--line);margin-top:60px;padding:30px 0;
font:.9rem system-ui,sans-serif}.cols{display:grid;
grid-template-columns:2fr 1fr 1fr 1fr;gap:20px}.cols a{display:block}
@media(max-width:640px){.cols{grid-template-columns:1fr 1fr}h1{font-size:2rem}}
"""


# ---------------------------------------------------------------- helpers ---
def esc(x):
    return html.escape(str(x)) if x is not None else ""


def load(name, default):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else default


def read_events():
    p = DATA / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def read_runs():
    runs = []
    logdir = ROOT / "logs"
    if logdir.exists():
        for f in sorted(logdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
            msgs = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
            if msgs:
                runs.append({"node": f.stem.rsplit("-", 1)[0], "msgs": msgs,
                             "mtime": f.stat().st_mtime})
    return runs


def evidence(path):
    if not path:
        return ""
    if path.startswith("http"):
        return f'<a href="{esc(path)}">source</a>'
    if path.startswith("refuter:"):
        return esc(path)
    return f'<a href="{REPO}/blob/main/{esc(path)}">{esc(path.split("/")[-1])}</a>'


def eqn(a):
    a1, a2, a3, a4, a6 = a

    def term(c, s):
        if c == 0:
            return ""
        coef = "" if (abs(c) == 1 and s) else str(abs(c))
        return (" − " if c < 0 else " + ") + coef + s

    return ("y²" + term(a1, "xy") + term(a3, "y") + " = x³"
            + term(a2, "x²") + term(a4, "x") + term(a6, ""))


def sym(status):
    return (f'<span class="sym" style="color:{COLOR.get(status, "#6e7781")}">'
            f'{SYM.get(status, "?")}</span>')


def item(n, reason=None):
    who = ""
    if n.get("agent"):
        who = f' · by {esc(n["agent"])}' + (f' ({esc(n["model"])})' if n.get("model") else "")
    lean = f' · <code>{esc(n["lean"])}</code>' if n.get("lean") else ""
    ev = f" · {evidence(n.get('evidence'))}" if n.get("evidence") else ""
    why = f'<div class="meta">Reason: {esc(reason)}</div>' if reason else ""
    return (f'<div class="item" id="{esc(n["id"])}">{sym(n["status"])}<b>{esc(n["title"])}</b>'
            f'<div>{esc(n["statement"])}</div><div class="meta">{esc(n["program"])}{lean}{who}{ev}'
            f'</div>{why}</div>')


# ------------------------------------------------------------------ shell ---
def shell(title, body, ctx):
    nav = ""
    for grp, links in NAV:
        if grp is None:
            nav += "".join(f'<a href="{h}">{t}</a>' for h, t in links)
        else:
            menu = "".join(f'<a href="{h}">{t}</a>' for h, t in links)
            nav += (f'<div class="grp" tabindex="0"><span>{grp} ▾</span>'
                    f'<div class="menu">{menu}</div></div>')
    working = ctx["working"]
    status = (f'<span><span class="dot on"></span>{working} agent(s) working on it now</span>'
              if working else '<span><span class="dot"></span>Agents idle right now</span>')
    built = ctx["built"]
    footer = f"""<footer><div class="wrap"><div class="cols">
<div><div class="logo">{SITE}</div><div class="meta">{TAGLINE}</div>
<div class="meta">Founded by {esc(FOUNDERS)}.</div></div>
<div><div class="label">Site</div><a href="/#map">Map</a><a href="/news/">News</a>
<a href="/programs/">Programs</a><a href="/how/">How it works</a></div>
<div><div class="label">About</div><a href="/about/">What this is</a>
<a href="/about/#questions">Questions people ask</a><a href="/contributors/">Contributors</a>
<a href="/sponsors/">Sponsors</a><a href="/prize/">Prize money</a></div>
<div><div class="label">Follow</div><a href="/feed.atom">RSS / Atom</a>
<a href="/follow/">Follow a program</a><a href="/join.txt">Connect your own agent</a></div>
</div><p class="meta">© 2026 {SITE} · Every ✓ is checked by the Lean kernel with an axiom
audit; numerical results are evidence, not proofs. · Built {built} ·
<a href="{REPO}">source &amp; full history</a></p></div></footer>"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · {SITE}</title>
<link rel="alternate" type="application/atom+xml" href="/feed.atom"><style>{CSS}</style></head>
<body><a class="skip" href="#main">Skip to content</a><header><div class="wrap">
<div class="top"><a class="logo" href="/">{SITE}<small>{TAGLINE}</small></a>
<a class="btn solid" href="/sponsors/">Sponsor us</a></div><nav>{nav}</nav>
<div class="strip">{status}<span>Join the effort: <code class="join">git clone {REPO}</code>
</span></div></div></header><main id="main" class="wrap">{body}</main>{footer}</body></html>"""


def write(path, title, body, ctx):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(shell(title, body, ctx))


# ------------------------------------------------------------------- main ---
def main():
    nodes = load("nodes.json", [])
    curves = load("curves.json", [])
    comps = load("computations.json", {})
    sponsors = load("sponsors.json", [])
    letters = load("letters.json", [])
    events = read_events()
    runs = read_runs()
    by = lambda *s: [n for n in nodes if n["status"] in s]
    last_reason = {e["node"]: e["reason"] for e in events}
    OUT.mkdir(parents=True, exist_ok=True)

    now = time.time()
    ctx = {"working": sum(1 for r in runs if now - r["mtime"] < 600),
           "built": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    audit = ROOT / "audit-report.txt"
    theorems = audit.read_text().count("depends on axioms") if audit.exists() else 0
    consistent = sum(c.get("bsd_numeric") == "consistent" for c in curves)
    checked = sorted(by("checked"), key=lambda n: n.get("updated_at", n["created_at"]),
                     reverse=True)
    grave = by("refuted", "dead")

    # -- Home ------------------------------------------------------------------
    legend = "".join(f'<span>{sym(s)}{LABEL[s]}</span>' for s in SYM)
    frontier_card = "".join(item(n) for n in checked[:5]) or "<p class='meta'>Nothing yet.</p>"
    grave_card = ("".join(item(n, last_reason.get(n["id"])) for n in grave[:5])
                  or "<p class='meta'>Nothing yet.</p>")
    last = events[-1] if events else None
    snapshot = (f'<p>{sym(last["to"])}<b>{esc(last["node"])}</b> → {esc(last["to"])}: '
                f'{esc(last["reason"])} <span class="meta">{esc(last["time"][:16])}</span></p>'
                if last else "<p class='meta'>No activity yet.</p>")
    search_data = json.dumps([{"id": n["id"], "t": n["title"], "s": n["statement"],
                               "p": n["program"], "st": n["status"]} for n in nodes],
                             ensure_ascii=False).replace("</", "<\\/")
    latest_sponsor = sponsors[-1] if sponsors else None
    total = sum(s.get("amount", 0) for s in sponsors)
    home = f"""
<h1>Does rank E(ℚ) = ord<sub>s=1</sub> L(E, s)?</h1>
<p class="verdict"><b>Verdict: open, being worked on now.</b></p>
<p class="sub">{TAGLINE} Every lemma, attempt, refutation and dead end is recorded here.</p>
<div class="row stat"><span><b>{len(runs)}</b>agent sessions so far</span>
<span><b>{ctx["working"]}</b>agents working now</span></div>
<div class="row"><a class="btn" href="/about/">What is BSD?</a>
<a class="btn solid" href="/live/">Watch it live</a>
<a class="btn" href="#" onclick="navigator.clipboard.writeText(location.origin);
this.textContent='Link copied';return false">Share this with someone</a></div>

<h2 class="label">Aiming at <a href="/about/#aim" title="What exactly?">ⓘ</a></h2>
<p>The <b>weak and strong Birch and Swinnerton-Dyer conjectures</b> over ℚ, as stated in
<a href="https://github.com/google-deepmind/formal-conjectures">formal-conjectures</a>
(<code>Millennium/BSD.lean</code>), with our own Lean statement <code>BsdProject.WeakBSD</code>.</p>

<h2 class="label">Latest snapshot</h2>{snapshot}
<input class="search" id="q" placeholder="Search lemmas, programs and curves  (press / )">
<div id="results"></div>

<h2 class="label">Legend</h2><div class="legend">{legend}</div>

<div class="row stat" style="margin-top:24px">
<span><b>{len(checked)}</b>lemmas checked</span><span><b>{len(by("refuted"))}</b>claims refuted</span>
<span><b>{len(by("dead"))}</b>approaches ruled dead</span>
<span><b>{theorems}</b>theorems audited</span>
<span><b>{consistent}/{len(curves)}</b>curves consistent with BSD</span></div>

<h2 id="map">Latest from the record</h2><div class="cards">
<div class="card"><h3>The frontier</h3><div class="meta">checked ·
<a href="/graveyard/">see the graveyard</a></div>{frontier_card}</div>
<div class="card"><h3>The graveyard</h3><div class="meta">in memoriam</div>{grave_card}</div>
</div>
<p class="meta">Every entry in the feed is a structured record: a lemma stated, an attempt
begun or ended, and the checker's verdict. <a href="/feed/">The whole feed →</a></p>
<p><a href="/map/">Open the full dependency map →</a></p>

<h2>Sponsors</h2><div class="cards"><div class="card"><div class="label">Latest</div>
{esc(latest_sponsor["name"]) + " · $" + esc(latest_sponsor.get("amount", "")) if latest_sponsor else "Be the first."}
</div><div class="card"><div class="label">Total</div><b>${total}</b></div></div>
<p><a href="/sponsors/">See all sponsors</a> · Any amount is welcome; it pays for agent time.</p>
<div class="cta"><h2>Back the attack on BSD</h2>
<a class="btn solid" href="/sponsors/">Become a sponsor</a></div>

<script>
const D={search_data};const q=document.getElementById('q'),r=document.getElementById('results');
const S={json.dumps(SYM, ensure_ascii=False)};
document.addEventListener('keydown',e=>{{if(e.key==='/'&&document.activeElement!==q)
{{e.preventDefault();q.focus()}}}});
q.addEventListener('input',()=>{{const v=q.value.toLowerCase().trim();r.innerHTML='';if(!v)return;
D.filter(n=>(n.id+n.t+n.s+n.p).toLowerCase().includes(v)).slice(0,12).forEach(n=>{{
const d=document.createElement('div');d.innerHTML='<b>'+S[n.st]+'</b> <a href="/programs/#'+n.id+
'">'+n.t.replace(/</g,'&lt;')+'</a> <span class="meta">'+n.p+'</span>';r.appendChild(d)}})}});
</script>"""
    write("index.html", "Home", home, ctx)

    # -- Map ---------------------------------------------------------------------
    lines = ["graph TD"]
    for n in nodes:
        t = n["title"].replace('"', "'")
        lines.append(f'  {n["id"]}["{SYM.get(n["status"], "?")} {t}"]:::{n["status"]}')
        for d in n["depends_on"]:
            lines.append(f"  {d} --> {n['id']}")
    for s, c in COLOR.items():
        lines.append(f"  classDef {s} stroke:{c},stroke-width:2px")
    write("map/index.html", "Map", f"""<h1>Map</h1><p class="sub">Every claim and what it
depends on. Arrows point from a result to the claims built on it.</p>
<div class="legend">{legend}</div><pre class="mermaid">{esc(chr(10).join(lines))}</pre>
<script type="module">import mermaid from
'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({{startOnLoad:true}});</script>""", ctx)

    # -- News ------------------------------------------------------------------------
    news = "".join(
        f'<div class="item">{sym(e["to"])}<b>{esc(e["node"])}</b>: '
        f'{esc(e["from"] or "new")} → {esc(e["to"])}<div>{esc(e["reason"])}</div>'
        f'<div class="meta">{esc(e["time"][:16])}</div></div>' for e in reversed(events[-40:]))
    write("news/index.html", "News", f"<h1>News</h1><p class='sub'>What changed, newest "
          f"first.</p>{news or '<p>No news yet.</p>'}", ctx)

    # -- Programs ------------------------------------------------------------------
    body = "<h1>Programs</h1><p class='sub'>Each line of attack, with every claim in it.</p>"
    for p in sorted({n["program"] for n in nodes}):
        ns = [n for n in nodes if n["program"] == p]
        counts = " · ".join(f"{sum(n['status'] == s for n in ns)} {LABEL[s]}"
                            for s in SYM if any(n["status"] == s for n in ns))
        body += (f'<h2 id="program-{esc(p)}">{esc(p)}</h2><p class="meta">{counts}</p>'
                 + "".join(item(n, last_reason.get(n["id"]) if n["status"] in
                                ("refuted", "dead") else None) for n in ns))
    write("programs/index.html", "Programs", body, ctx)

    # -- Curves --------------------------------------------------------------------
    rows = ""
    for c in curves:
        d = comps.get(c["label"], {})
        v = c.get("bsd_numeric", "not computed")
        col = "#1a7f37" if v == "consistent" else "#9a6700"
        rows += (f'<tr><td><b>{esc(c["label"])}</b><div class="meta">{esc(eqn(c["ainvs"]))}</div>'
                 f'</td><td>{esc(c.get("conductor", ""))}</td>'
                 f'<td>{esc(d.get("rank_lower", c.get("rank", "")))}</td>'
                 f'<td>{esc(d.get("analytic_rank", ""))}</td><td>{esc(d.get("torsion", ""))}</td>'
                 f'<td>{esc(d.get("tamagawa", ""))}</td><td>{d.get("regulator", 0):.6f}</td>'
                 f'<td>{esc(c.get("sha_an", ""))}</td><td style="color:{col}">{esc(v)}</td></tr>')
    write("curves/index.html", "Curves", f"""<h1>Curves</h1><p class="sub">Both sides of the full
BSD formula, computed with PARI/GP. Numerical evidence, not proofs.</p><table><tr><th>Curve</th>
<th>Conductor</th><th>Rank</th><th>Analytic rank</th><th>Torsion</th><th>Tamagawa</th>
<th>Regulator</th><th>Sha</th><th>BSD</th></tr>{rows}</table>""", ctx)

    # -- Papers ----------------------------------------------------------------------
    papers_dir = ROOT / "docs"
    papers = sorted(papers_dir.glob("*.md")) if papers_dir.exists() else []
    plist = "".join(f'<div class="item"><a href="{REPO}/blob/main/docs/{esc(p.name)}">'
                    f'{esc(p.stem.replace("-", " ").replace("_", " "))}</a></div>' for p in papers)
    write("papers/index.html", "Papers", "<h1>Papers</h1><p class='sub'>Human-readable "
          "write-ups of what the agents found. Add Markdown files to <code>docs/</code>.</p>"
          + (plist or "<p>No papers yet.</p>"), ctx)
    write("papers/how/index.html", "How papers are written", """<h1>How papers are written</h1>
<p>A paper is only written about results the Lean checker has accepted. Agents draft, a human
edits, and every theorem cited links to its Lean source and its axiom audit. Numerical results
are reported as evidence and labelled as such. Drafts go to arXiv when a result is worth it.</p>""",
          ctx)

    # -- Letters ---------------------------------------------------------------------
    lt = "".join(f'<div class="item"><b>{esc(l.get("from", ""))}</b> '
                 f'<span class="meta">{esc(l.get("date", ""))}</span>'
                 f'<div>{esc(l.get("text", ""))}</div></div>' for l in reversed(letters))
    write("letters/index.html", "Letters", "<h1>Letters</h1><p class='sub'>Advice, corrections "
          "and questions from people following the work. Add them to "
          "<code>data/letters.json</code>.</p>" + (lt or "<p>No letters yet.</p>"), ctx)

    # -- Graveyard -------------------------------------------------------------------
    write("graveyard/index.html", "Graveyard", "<h1>The graveyard</h1><p class='sub'>In "
          "memoriam: refuted claims and approaches ruled dead, with the reason they died.</p>"
          + ("".join(item(n, last_reason.get(n["id"])) for n in grave) or "<p>Empty.</p>"), ctx)

    # -- Live ----------------------------------------------------------------------------
    goals = {n["id"]: n.get("lean_goal", "") for n in nodes}
    live = ("<h1>Live</h1><p class='sub'>Every agent conversation, newest first. "
            "This page refreshes every 20 seconds.</p>")
    for i, r in enumerate(runs[:30]):
        msgs = r["msgs"]
        ok = msgs[-1]["feedback"] == "OK"
        active = now - r["mtime"] < 600 and not ok
        badge = (f'{sym("checked")}proved' if ok else
                 f'{sym("in_progress")}working' if active else f'{sym("dead")}gave up')
        loop_msgs = msgs
        if msgs[0].get("role") == "Proposer":
            badge = f'{sym("conjecture")}new claims proposed'
            chat = ('<div class="msg planner"><b>Planner → Proposer</b><pre>The queue is '
                    'empty. Propose new claims for the team to work on.</pre></div>')
            for m in msgs:
                chat += (f'<div class="msg agent"><b>Proposer · {esc(m["model"])}</b>'
                         f'<pre>{esc(m["reply"][-3000:])}</pre></div>'
                         f'<div class="msg checker"><b>Validator</b>'
                         f'<pre>{esc(m["feedback"][-2000:])}</pre></div>')
            chat += ('<div class="msg planner"><b>Planner → Refuter</b><pre>Test the new '
                     'claims before anyone tries to prove them.</pre></div>')
            loop_msgs = []
        else:
            chat = (f'<div class="msg planner"><b>Planner → Prover</b>'
                    f'<pre>Prove: {esc(goals.get(r["node"], r["node"]))}</pre></div>')
        for m in loop_msgs:
            chat += (f'<div class="msg agent"><b>Prover · {esc(m["model"])} · attempt '
                     f'{m["attempt"]}</b><pre>{esc(m["reply"][-3000:])}</pre></div>')
            chat += ('<div class="msg ok"><b>Lean checker</b><pre>✓ Compiles. Sent to the full '
                     'axiom audit.</pre></div>' if m["feedback"] == "OK" else
                     f'<div class="msg checker"><b>Lean checker</b>'
                     f'<pre>{esc(m["feedback"][-2000:])}</pre></div>')
        live += (f'<details{" open" if i == 0 else ""}><summary>{badge} · <b>{esc(r["node"])}</b> · '
                 f'{len(msgs)} attempt(s) · {esc(msgs[-1]["time"][:16])}</summary>{chat}</details>')
    if not runs:
        live += "<p>No agent sessions yet.</p>"
    live += "<script>setTimeout(()=>location.reload(),20000)</script>"
    write("live/index.html", "Live", live, ctx)

    # -- Feed (HTML + Atom) ---------------------------------------------------------
    feed = "".join(
        f'<tr><td class="meta">{esc(e["time"][:16])}</td><td>{sym(e["to"])}{esc(e["node"])}</td>'
        f'<td>{esc(e["from"] or "new")} → {esc(e["to"])}</td><td>{esc(e["reason"])}</td></tr>'
        for e in reversed(events))
    write("feed/index.html", "Feed", f"""<h1>The whole feed</h1><p class="sub">Every status
change, as a structured record. Also as <a href="/feed.atom">Atom</a>.</p>
<table><tr><th>Time</th><th>Claim</th><th>Change</th><th>Reason</th></tr>{feed}</table>""", ctx)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    entries = "".join(
        f"<entry><title>{esc(e['node'])}: {esc(e['to'])}</title>"
        f"<id>{REPO}#{esc(e['node'])}-{esc(e['time'])}</id>"
        f"<updated>{esc(e['time'][:16])}:00Z</updated>"
        f"<summary>{esc(e['reason'])}</summary></entry>" for e in reversed(events[-50:]))
    (OUT / "feed.atom").write_text(f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>{esc(SITE)}</title><id>{REPO}</id>
<updated>{stamp}</updated>{entries}</feed>""")

    # -- Contributors -----------------------------------------------------------------
    people = {}
    for n in nodes:
        if n["status"] == "checked" and n.get("agent"):
            key = n["agent"] + (f" ({n['model']})" if n.get("model") else "")
            people[key] = people.get(key, 0) + 1
    crow = "".join(f"<tr><td>{esc(k)}</td><td>{v}</td></tr>"
                   for k, v in sorted(people.items(), key=lambda kv: -kv[1]))
    write("contributors/index.html", "Contributors", f"""<h1>Contributors</h1><p class="sub">
Humans and agents, ranked by results accepted by the checker.</p><table><tr><th>Contributor</th>
<th>Checked results</th></tr>{crow}</table><p><a href="/join.txt">Connect your own agent →</a></p>""",
          ctx)

    # -- Sponsors ---------------------------------------------------------------------
    srow = "".join(f'<tr><td>{esc(s.get("name", ""))}</td><td>${esc(s.get("amount", ""))}</td>'
                   f'<td class="meta">{esc(s.get("date", ""))}</td></tr>' for s in reversed(sponsors))
    write("sponsors/index.html", "Sponsors", f"""<h1>Sponsors</h1><p class="sub">Sponsorship
pays for agent time. Any amount is welcome. Total so far: <b>${total}</b>.</p>
<table><tr><th>Sponsor</th><th>Amount</th><th>Date</th></tr>{srow}</table>
<p class="meta">Payments are not set up yet. Add sponsors to <code>data/sponsors.json</code>.</p>""",
          ctx)

    # -- About (What this is + Questions) ---------------------------------------------
    write("about/index.html", "What this is", f"""<h1>What this is</h1>
<p>{TAGLINE} The Birch and Swinnerton-Dyer conjecture says that for an elliptic curve E over
ℚ, the rank of its group of rational points equals the order of vanishing of its L-function at
s = 1, and that the leading coefficient there is given by an exact formula. It is one of the
seven Clay Millennium Prize Problems.</p>
<h2 id="aim">What exactly are we aiming at?</h2><p>The weak and strong BSD statements in
<a href="https://github.com/google-deepmind/formal-conjectures">formal-conjectures</a>
(<code>FormalConjectures/Millennium/BSD.lean</code>) and our own statement
<code>BsdProject.WeakBSD</code>, built on mathlib's <code>WeierstrassCurve.LSeries</code>.</p>
<h2 id="questions">Questions people ask</h2>
<p><b>Has it been solved?</b> No. The conjecture is open. What is checked here are small,
verified steps, and the record of what failed.</p>
<p><b>What does “checked” mean?</b> The Lean proof checker accepted the proof, and an axiom
audit confirmed it uses only Lean's three standard axioms: no <code>sorry</code>, no shortcuts.</p>
<p><b>Are the numbers proofs?</b> No. Computations with PARI/GP are evidence, labelled as such.</p>
<p><b>Can I help?</b> Yes. <a href="/join.txt">Connect your own agent</a> or
<a href="/sponsors/">sponsor agent time</a>.</p>""", ctx)

    write("how/index.html", "How it works", """<h1>How it works</h1>
<p><b>Planner.</b> Picks the next open claim whose dependencies are checked, within a daily
budget, and buries claims that fail too often.</p>
<p><b>Refuter.</b> Tests every claim with exact arithmetic before money is spent on it. A false
claim goes straight to the graveyard.</p>
<p><b>Prover.</b> Writes a Lean proof, reads the compiler's errors, and tries again.</p>
<p><b>Checker.</b> The Lean kernel plus an axiom audit. It is the only judge of “checked”.</p>
<p><b>Computation.</b> PARI/GP computes both sides of the BSD formula for each curve.</p>
<p>Everything is logged: every prompt, every reply, every verdict. See <a href="/live/">Live</a>.
</p>""", ctx)

    write("prize/index.html", "Prize money", """<h1>Prize money</h1><p>The Clay Mathematics
Institute offers US$1,000,000 for a resolution of the Birch and Swinnerton-Dyer conjecture. Under
its rules, a solution must be published in a qualifying journal and be generally accepted for
two years. This project makes no claim to the prize. Its aim is honest, checkable progress.</p>
<p><a href="https://www.claymath.org/millennium/birch-and-swinnerton-dyer-conjecture/">The
official problem (Clay Mathematics Institute)</a></p>""", ctx)

    progs = "".join(f'<li><a href="/programs/#program-{esc(p)}">{esc(p)}</a></li>'
                    for p in sorted({n["program"] for n in nodes}))
    write("follow/index.html", "Follow", f"""<h1>Follow</h1><p>Subscribe to the
<a href="/feed.atom">Atom feed</a> in any feed reader, or watch the
<a href="{REPO}">repository</a> on GitHub for every change.</p><h2>Follow a program</h2>
<ul>{progs}</ul>""", ctx)

    # -- join.txt ------------------------------------------------------------------------
    (OUT / "join.txt").write_text(f"""{SITE}: connect your own agent

1. Clone the project:  git clone {REPO}
2. Pick an open claim in data/nodes.json that has a "lean_goal".
3. Prove it in Lean under bsd_project/BsdProject/Agent/<id>.lean
   No sorry, no custom axioms. ./scripts/audit.sh must say PASS.
4. Open a pull request. The audit decides; nothing else does.
""")
    pages = sum(1 for _ in OUT.rglob("*") if _.is_file())
    print(f"Built {pages} files into site/dist/  (open http://localhost:8000)")


if __name__ == "__main__":
    main()