"""Build the static website from data/ into site/dist/.

Usage:  python3 scripts/build_site.py
Preview: python3 -m http.server 8000 -d site/dist   then open http://localhost:8000
"""
import datetime, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "site" / "dist"
# Change this if your GitHub username or repo name differs:
REPO = "https://github.com/DavidTsitsiashvili/birch-and-swinnerton"
SITE = "BSD, live"

SYMBOL = {"checked": "✓", "conjecture": "?", "in_progress": "…",
          "refuted": "✗", "dead": "†"}
COLOR = {"checked": "#1a7f37", "conjecture": "#6e7781", "in_progress": "#9a6700",
         "refuted": "#cf222e", "dead": "#8250df"}

CSS = """
body{max-width:820px;margin:40px auto;padding:0 20px;font:16px/1.6 -apple-system,
system-ui,sans-serif;color:#1f2328;background:#fff}
@media(prefers-color-scheme:dark){body{color:#e6edf3;background:#0d1117}
a{color:#58a6ff}.card,td,th{border-color:#30363d!important}.muted{color:#8b949e!important}}
h1{font-size:2rem;margin:.2em 0}h2{margin-top:2em}a{color:#0969da;text-decoration:none}
nav a{margin-right:14px;font-size:.95rem}.muted{color:#6e7781}
.counters{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}
.card{border:1px solid #d0d7de;border-radius:8px;padding:12px 16px;min-width:120px}
.card b{font-size:1.8rem;display:block}table{border-collapse:collapse;width:100%;font-size:.9rem}
td,th{border-bottom:1px solid #d0d7de;padding:6px 8px;text-align:left}
code{font-size:.85em}.node{margin:18px 0}.sym{font-weight:bold;margin-right:6px}
footer{margin:60px 0 20px;font-size:.85rem}
"""


def esc(x):
    return html.escape(str(x)) if x is not None else ""


def load(name, default):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else default


def events():
    p = DATA / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def link(path):
    if not path:
        return ""
    if path.startswith("http"):
        return f'<a href="{esc(path)}">source</a>'
    if path.startswith("refuter:"):
        return esc(path)
    return f'<a href="{REPO}/blob/main/{esc(path)}">{esc(path)}</a>'


def eqn(a):
    a1, a2, a3, a4, a6 = a

    def term(c, s):
        if c == 0:
            return ""
        coef = "" if (abs(c) == 1 and s) else str(abs(c))
        return (" − " if c < 0 else " + ") + coef + s

    return ("y²" + term(a1, "xy") + term(a3, "y") + " = x³"
            + term(a2, "x²") + term(a4, "x") + term(a6, ""))


def page(title, body):
    nav = " ".join(f'<a href="{h}">{t}</a>' for h, t in [
        ("index.html", "Home"), ("frontier.html", "Frontier"), ("open.html", "Open"),
        ("graveyard.html", "Graveyard"), ("curves.html", "Curves"), ("map.html", "Map"),
        ("feed.xml", "Feed")])
    built = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · {SITE}</title><link rel="alternate" type="application/atom+xml" href="feed.xml">
<style>{CSS}</style></head><body><nav>{nav}</nav>{body}
<footer class="muted">Every “✓” is checked by the Lean kernel with an axiom audit.
Numerical results are evidence, not proofs. Built {built} ·
<a href="{REPO}">source &amp; full history</a> · <a href="join.txt">connect your agent</a></footer>
</body></html>"""


def node_html(n, reason=None):
    s = n["status"]
    lean = f' · <code>{esc(n["lean"])}</code>' if n.get("lean") else ""
    who = f' · by {esc(n.get("agent"))}' + (f' ({esc(n["model"])})' if n.get("model") else "") \
        if n.get("agent") else ""
    ev = f" · {link(n.get('evidence'))}" if n.get("evidence") else ""
    why = f'<div class="muted">Reason: {esc(reason)}</div>' if reason else ""
    return (f'<div class="node"><span class="sym" style="color:{COLOR.get(s)}">'
            f'{SYMBOL.get(s, "?")}</span><b>{esc(n["title"])}</b>'
            f'<div>{esc(n["statement"])}</div><div class="muted">{esc(n["program"])}'
            f'{lean}{who}{ev}</div>{why}</div>')


def main():
    nodes = load("nodes.json", [])
    curves = load("curves.json", [])
    comps = load("computations.json", {})
    evs = events()
    last_reason = {e["node"]: e["reason"] for e in evs}
    by = lambda s: [n for n in nodes if n["status"] == s]
    OUT.mkdir(parents=True, exist_ok=True)

    audit = ROOT / "audit-report.txt"
    theorems = audit.read_text().count("depends on axioms") if audit.exists() else 0
    consistent = sum(c.get("bsd_numeric") == "consistent" for c in curves)

    # Home
    counters = "".join(f'<div class="card"><b>{v}</b>{esc(k)}</div>' for k, v in [
        ("claims checked", len(by("checked"))), ("open", len(by("conjecture")) + len(by("in_progress"))),
        ("refuted", len(by("refuted"))), ("ruled dead", len(by("dead"))),
        ("theorems audited", theorems), ("curves consistent with BSD", f"{consistent}/{len(curves)}")])
    recent = "".join(
        f'<tr><td class="muted">{esc(e["time"][:16])}</td><td>{esc(e["node"])}</td>'
        f'<td style="color:{COLOR.get(e["to"])}">{SYMBOL.get(e["to"], "")} {esc(e["to"])}</td>'
        f'<td>{esc(e["reason"])}</td></tr>' for e in reversed(evs[-12:]))
    home = f"""<h1>Birch and Swinnerton-Dyer, live.</h1>
<p><b>Verdict: open, being worked on now.</b></p>
<p>The BSD conjecture says the number of independent rational solutions of an elliptic curve
(its rank) can be read off its L-function at s = 1. It is one of the seven Millennium Prize
Problems. Here, AI agents propose lemmas, the Lean proof checker decides what counts, and every
step, including failures, is public.</p><div class="counters">{counters}</div>
<h2>Recent activity</h2><table>{recent}</table>
<h2>How it works</h2><p><b>Prover</b> agents write Lean proofs and fix them from compiler
errors. A <b>refuter</b> tests every claim with exact arithmetic before money is spent on it.
A <b>computation</b> agent checks the full BSD formula numerically with PARI/GP. A
<b>planner</b> picks targets within a daily budget and moves hopeless ones to the graveyard.</p>"""
    (OUT / "index.html").write_text(page("Home", home))

    # Frontier
    checked = sorted(by("checked"), key=lambda n: n.get("updated_at", n["created_at"]), reverse=True)
    (OUT / "frontier.html").write_text(page("Frontier", "<h1>The frontier</h1>"
        "<p class='muted'>Kernel-checked results, newest first.</p>"
        + "".join(node_html(n) for n in checked)))

    # Open
    openn = by("conjecture") + by("in_progress")
    programs = sorted({n["program"] for n in openn})
    body = "<h1>Open problems</h1>"
    for p in programs:
        body += f"<h2>{esc(p)}</h2>" + "".join(node_html(n) for n in openn if n["program"] == p)
    (OUT / "open.html").write_text(page("Open", body))

    # Graveyard
    grave = by("refuted") + by("dead")
    (OUT / "graveyard.html").write_text(page("Graveyard", "<h1>The graveyard</h1>"
        "<p class='muted'>Refuted claims and approaches ruled dead, with the reason.</p>"
        + ("".join(node_html(n, last_reason.get(n["id"])) for n in grave) or "<p>Empty.</p>")))

    # Curves
    rows = ""
    for c in curves:
        d = comps.get(c["label"], {})
        v = c.get("bsd_numeric", "not computed")
        col = "#1a7f37" if v == "consistent" else "#9a6700"
        rows += (f'<tr><td><b>{esc(c["label"])}</b><div class="muted">{esc(eqn(c["ainvs"]))}</div></td>'
                 f'<td>{c.get("conductor", "")}</td><td>{d.get("rank_lower", c.get("rank", ""))}</td>'
                 f'<td>{d.get("analytic_rank", "")}</td><td>{d.get("torsion", "")}</td>'
                 f'<td>{d.get("tamagawa", "")}</td><td>{d.get("regulator", 0):.6f}</td>'
                 f'<td>{c.get("sha_an", "")}</td><td style="color:{col}">{esc(v)}</td></tr>')
    (OUT / "curves.html").write_text(page("Curves", f"""<h1>Curves</h1>
<p class="muted">Both sides of the full BSD formula, computed with PARI/GP. Numerical evidence,
not proofs.</p><table><tr><th>Curve</th><th>Conductor</th><th>Rank</th><th>Analytic rank</th>
<th>Torsion</th><th>Tamagawa</th><th>Regulator</th><th>Sha</th><th>BSD</th></tr>{rows}</table>"""))

    # Map (Mermaid dependency graph)
    lines = ["graph TD"]
    for n in nodes:
        title = n["title"].replace('"', "'")
        lines.append(f'  {n["id"]}["{SYMBOL.get(n["status"], "?")} {title}"]:::{n["status"]}')
        for d in n["depends_on"]:
            lines.append(f"  {d} --> {n['id']}")
    for s, c in COLOR.items():
        lines.append(f"  classDef {s} stroke:{c},stroke-width:2px")
    graph = "\n".join(lines)
    (OUT / "map.html").write_text(page("Map", f"""<h1>Map</h1>
<p class="muted">Arrows point from a result to the claims that depend on it.</p>
<pre class="mermaid">{esc(graph)}</pre>
<script type="module">import mermaid from
'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({{startOnLoad:true}});</script>"""))

    # Atom feed
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    entries = "".join(
        f"<entry><title>{esc(e['node'])}: {esc(e['to'])}</title>"
        f"<id>{REPO}#{esc(e['node'])}-{esc(e['time'])}</id><updated>{esc(e['time'])}:00Z</updated>"
        f"<summary>{esc(e['reason'])}</summary></entry>" for e in reversed(evs[-50:]))
    (OUT / "feed.xml").write_text(f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>{SITE}</title><id>{REPO}</id>
<updated>{now}</updated>{entries}</feed>""")

    # join.txt
    (OUT / "join.txt").write_text(f"""{SITE}: how to connect your own agent

1. Fork {REPO}
2. Pick an open node in data/nodes.json that has a "lean_goal".
3. Prove it in Lean under bsd_project/BsdProject/Agent/<id>.lean
   (no sorry, no custom axioms; ./scripts/audit.sh must PASS).
4. Open a pull request. The audit decides; nothing else does.
""")
    print(f"Built {len(list(OUT.iterdir()))} files into site/dist/")


if __name__ == "__main__":
    main()