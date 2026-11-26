"""Prover agent: picks an open node with a `lean_goal`, asks Claude for a
Lean proof, checks it with Lean, retries on errors, and records the result.

Usage:  python3 agents/prover.py            (first open target)
        python3 agents/prover.py NODE_ID    (a specific target)
"""
import datetime, json, os, re, subprocess, sys, time
from pathlib import Path
import anthropic

ROOT = Path(__file__).resolve().parent.parent
LEAN = ROOT / "bsd_project"
AGENT_DIR = LEAN / "BsdProject" / "Agent"
MAIN = LEAN / "BsdProject.lean"
NODES = ROOT / "data" / "nodes.json"
EVENTS = ROOT / "data" / "events.jsonl"
LOGS = ROOT / "logs"
MODEL = os.environ.get("BSD_MODEL", "claude-sonnet-5-5")
MAX_ATTEMPTS = int(os.environ.get("BSD_MAX_ATTEMPTS", "5"))

SYSTEM = """You are an expert in Lean 4 and mathlib. You write complete, compiling Lean files.
Rules:
- Reply with ONE complete Lean file inside a ```lean code block.
- Put the theorem inside `namespace BsdProject` ... `end BsdProject`.
- The file must contain the theorem statement EXACTLY as given, character for character.
- Never use `sorry`, `admit`, `axiom`, or `native_decide`.
- Project definitions are available via `import BsdProject.Curves`:
  E37 and E389 are `WeierstrassCurve ℚ` (LMFDB 37.a1 and 389.a1).
- mathlib is recent (Lean v4.36). Elliptic curve files live under
  Mathlib.AlgebraicGeometry.EllipticCurve (e.g. ...EllipticCurve.Affine.Point).
- If a lemma name is wrong, try another approach (simp, norm_num, ring_nf, unfold)."""


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def lean_check(path):
    r = subprocess.run(["lake", "env", "lean", str(path.relative_to(LEAN))],
                       cwd=LEAN, capture_output=True, text=True, timeout=900)
    out = r.stdout + r.stderr
    return r.returncode == 0 and "error:" not in out, out


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    nodes = json.loads(NODES.read_text())
    node = next((n for n in nodes if n.get("lean_goal")
                 and n["status"] in ("conjecture", "in_progress")
                 and (wanted is None or n["id"] == wanted)), None)
    if node is None:
        print("No open node with a lean_goal."); return

    goal, name = node["lean_goal"].strip(), node["id"]
    thm = re.match(r"theorem\s+(\S+)", goal).group(1)
    AGENT_DIR.mkdir(exist_ok=True); LOGS.mkdir(exist_ok=True)
    path = AGENT_DIR / f"{name}.lean"
    log = LOGS / f"{name}-{int(time.time())}.jsonl"
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content":
                 f"Prove this in Lean 4 + mathlib:\n\n{goal}\n\nMeaning: {node['statement']}"}]
    tokens = 0
    print(f"Target: {name}  |  model: {MODEL}")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"  attempt {attempt}/{MAX_ATTEMPTS} ...", flush=True)
        resp = client.messages.create(model=MODEL, max_tokens=4000,
                                      system=SYSTEM, messages=messages)
        text = "".join(b.text for b in resp.content if b.type == "text")
        tokens += resp.usage.input_tokens + resp.usage.output_tokens
        m = re.search(r"```lean\s*\n(.*?)```", text, re.S)
        code, ok, out = (m.group(1) if m else None), False, ""

        if code is None:
            feedback = "No ```lean block found. Reply with one complete Lean file."
        elif re.search(r"\b(sorry|admit|axiom|native_decide)\b", code):
            feedback = "Forbidden: sorry/admit/axiom/native_decide. Give a real proof."
        elif goal not in code:
            feedback = f"The file must contain this statement exactly:\n{goal}"
        else:
            path.write_text(code)
            ok, out = lean_check(path)
            feedback = "OK" if ok else ("Lean errors:\n" + out[-4000:] +
                                        "\nReply with the complete corrected file.")

        with log.open("a") as f:
            f.write(json.dumps({"time": now(), "attempt": attempt, "model": MODEL,
                                "reply": text, "feedback": feedback},
                               ensure_ascii=False) + "\n")
        if ok:
            break
        messages += [{"role": "assistant", "content": text},
                     {"role": "user", "content": feedback}]

    if ok:
        # Hook the new file into the project, then require the full audit to pass.
        old = MAIN.read_text()
        imp = f"import BsdProject.Agent.{name}"
        if imp not in old:
            MAIN.write_text(old.rstrip("\n") + "\n" + imp + "\n")
        audit = subprocess.run([str(ROOT / "scripts" / "audit.sh")], cwd=ROOT)
        if audit.returncode != 0:
            MAIN.write_text(old); ok = False
            print("Proof compiled but the audit failed; not recorded as checked.")

    old_status = node["status"]
    if ok:
        node.update(status="checked", lean=f"BsdProject.{thm}", agent="prover",
                    model=MODEL, evidence=str(path.relative_to(ROOT)),
                    updated_at=now())
        NODES.write_text(json.dumps(nodes, ensure_ascii=False, indent=2))
        reason = f"Proved by prover agent ({MODEL}) in {attempt} attempt(s), audit PASS"
    else:
        reason = f"Prover agent failed after {MAX_ATTEMPTS} attempts"
    with EVENTS.open("a") as f:
        f.write(json.dumps({"time": now(), "node": name, "from": old_status,
                            "to": node["status"], "reason": reason},
                           ensure_ascii=False) + "\n")
    print(("SUCCESS: " if ok else "FAILED: ") + reason)
    print(f"Tokens used: {tokens}  |  log: {log.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
