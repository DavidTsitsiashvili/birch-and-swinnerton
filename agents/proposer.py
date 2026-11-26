"""Proposer agent: when the queue runs dry, asks Claude to propose new small,
Lean-provable claims about the project's curves. Every proposal is validated
here, and the refuter tests it before anyone tries to prove it.

Usage:  python3 agents/proposer.py [how_many]
"""
import datetime, json, os, re, sys, time
from pathlib import Path
import anthropic

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data" / "nodes.json"
CURVES = ROOT / "data" / "curves.json"
EVENTS = ROOT / "data" / "events.jsonl"
LOGS = ROOT / "logs"
MODEL = os.environ.get("BSD_MODEL", "claude-sonnet-5-5")

# Curves that exist as Lean definitions in bsd_project/BsdProject/Curves.lean
LEAN_NAMES = {"37.a1": "E37", "389.a1": "E389"}

SYSTEM = """You are the proposer in a team of AI agents working on the Birch and
Swinnerton-Dyer conjecture in Lean 4 + mathlib. Propose small, concrete claims that a
prover agent can check in Lean in a few minutes. They may be true or false: a refuter
tests them first, and false ones go to the graveyard, which is fine.

Allowed kinds of claim (use ONLY these):
1. A point lies on a curve.
   lean_goal: "theorem <id> : <E>.toAffine.Equation <x> <y>"
   check: {"type": "on_curve", "curve": "<label>", "point": [x, y]}
2. A point is a nonsingular point of a curve.
   lean_goal: "theorem <id> : <E>.toAffine.Nonsingular <x> <y>"
   check: {"type": "on_curve", "curve": "<label>", "point": [x, y]}
Write negative numbers in Lean with parentheses, e.g. (-1).
Use only integer coordinates. <E> must be one of the Lean names given.

Reply with a short explanation of your reasoning (2-4 sentences, as if talking to
your teammates), then a ```json block containing a list of objects with keys:
id, title, statement, lean_goal, check. The id must be letters, digits and
underscores, and must equal the theorem name in lean_goal."""


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def validate(p, existing, curves):
    need = {"id", "title", "statement", "lean_goal", "check"}
    if not isinstance(p, dict) or not need <= set(p):
        return "missing fields"
    if not re.fullmatch(r"[A-Za-z0-9_]+", str(p["id"])):
        return "bad id"
    if p["id"] in existing:
        return "duplicate id"
    m = re.fullmatch(r"theorem (\w+) : (\w+)\.toAffine\.(Equation|Nonsingular) (\S+) (\S+)",
                     p["lean_goal"].strip())
    if not m or m.group(1) != p["id"]:
        return "lean_goal not in an allowed form"
    c = p["check"]
    if c.get("type") != "on_curve" or c.get("curve") not in curves:
        return "bad check"
    if LEAN_NAMES.get(c["curve"]) != m.group(2):
        return "Lean name does not match the curve"
    try:
        x, y = (int(v) for v in c["point"])
    except Exception:
        return "point must be two integers"
    lx, ly = (s.strip("()") for s in (m.group(4), m.group(5)))
    if (lx, ly) != (str(x), str(y)):
        return "lean_goal point differs from check point"
    return None


def main():
    how_many = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    nodes = json.loads(NODES.read_text())
    curves = {c["label"]: c for c in json.loads(CURVES.read_text()) if c["label"] in LEAN_NAMES}
    existing = {n["id"] for n in nodes}
    recent = [f'{n["id"]} [{n["status"]}]: {n.get("lean_goal", "")}'
              for n in nodes if n.get("lean_goal")][-40:]
    curve_text = "\n".join(f'- {lab} (Lean name {LEAN_NAMES[lab]}): coefficients '
                           f'[a1,a2,a3,a4,a6] = {c["ainvs"]}, rank {c.get("rank")}'
                           for lab, c in curves.items())
    prompt = (f"Curves you may use:\n{curve_text}\n\nClaims already on the board "
              f"(do not repeat them):\n" + "\n".join(recent) +
              f"\n\nPropose {how_many} new claims. Prefer points that are not on the board yet; "
              "nonsingularity claims for points already proved to lie on a curve are good next steps.")

    LOGS.mkdir(exist_ok=True)
    log = LOGS / f"proposer-{int(time.time())}.jsonl"
    client = anthropic.Anthropic()
    resp = client.messages.create(model=MODEL, max_tokens=2000, system=SYSTEM,
                                  messages=[{"role": "user", "content": prompt}])
    text = "".join(b.text for b in resp.content if b.type == "text")
    tokens = resp.usage.input_tokens + resp.usage.output_tokens

    accepted, rejected = [], []
    m = re.search(r"```json\s*\n(.*?)```", text, re.S)
    try:
        proposals = json.loads(m.group(1)) if m else []
    except json.JSONDecodeError:
        proposals = []
    for p in proposals:
        why = validate(p, existing, curves)
        if why:
            rejected.append(f'{p.get("id", "?")}: {why}')
            continue
        existing.add(p["id"])
        dep = [d for d in (f'{LEAN_NAMES[p["check"]["curve"]]}_elliptic',) if d in existing]
        nodes.append({"id": p["id"], "title": p["title"], "statement": p["statement"],
                      "lean": None, "lean_goal": p["lean_goal"].strip(), "check": p["check"],
                      "status": "conjecture", "program": "foundations", "depends_on": dep,
                      "agent": "proposer", "model": MODEL, "evidence": None,
                      "created_at": now()})
        accepted.append(p["id"])

    if accepted:
        NODES.write_text(json.dumps(nodes, ensure_ascii=False, indent=2))
        with EVENTS.open("a") as f:
            for a in accepted:
                f.write(json.dumps({"time": now(), "node": a, "from": None, "to": "conjecture",
                                    "reason": f"Proposed by proposer agent ({MODEL})"},
                                   ensure_ascii=False) + "\n")
    feedback = (f"Accepted {len(accepted)}: {', '.join(accepted) or 'none'}"
                + (f"\nRejected {len(rejected)}:\n" + "\n".join(rejected) if rejected else ""))
    with log.open("w") as f:
        f.write(json.dumps({"time": now(), "attempt": 1, "role": "Proposer", "model": MODEL,
                            "reply": text, "feedback": feedback}, ensure_ascii=False) + "\n")
    print(feedback)
    print(f"Tokens used: {tokens}  |  log: {log.relative_to(ROOT)}")


if __name__ == "__main__":
    main()