"""Planner: runs the refuter, then the prover on open targets in priority
order, within a daily token budget. Moves hopeless targets to the graveyard.

Usage:  python3 agents/planner.py
Settings (optional environment variables):
  BSD_DAILY_TOKENS  daily token cap            (default 200000)
  BSD_MAX_RUNS      failed runs before 'dead'  (default 3)
  BSD_MAX_TARGETS   targets per planner run    (default 10)
"""
import datetime, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data" / "nodes.json"
EVENTS = ROOT / "data" / "events.jsonl"
BUDGET = ROOT / "data" / "budget.json"
DAILY_TOKENS = int(os.environ.get("BSD_DAILY_TOKENS", "200000"))
MAX_RUNS = int(os.environ.get("BSD_MAX_RUNS", "3"))
MAX_TARGETS = int(os.environ.get("BSD_MAX_TARGETS", "10"))
OPEN = ("conjecture", "in_progress")


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def today():
    return datetime.date.today().isoformat()


def failures(node_id):
    if not EVENTS.exists():
        return 0
    count = 0
    for line in EVENTS.read_text().splitlines():
        if line.strip():
            e = json.loads(line)
            if e["node"] == node_id and e["reason"].startswith("Prover agent failed"):
                count += 1
    return count


def run(script, *args):
    return subprocess.run([sys.executable, script, *args], cwd=ROOT,
                          capture_output=True, text=True)


def main():
    print("== 1. Refuter ==")
    r = run("agents/refuter.py")
    lines = r.stdout.strip().splitlines()
    print("  " + (lines[-1] if lines else r.stderr.strip()))
    if r.returncode != 0:
        print(r.stdout)
        print("STOP: the refuter found conflicts. A human must look before any proving.")
        sys.exit(1)

    print("== 2. Graveyard ==")
    nodes = json.loads(NODES.read_text())
    buried = 0
    for n in nodes:
        if n.get("lean_goal") and n["status"] in OPEN and failures(n["id"]) >= MAX_RUNS:
            old = n["status"]
            n.update(status="dead", updated_at=now())
            with EVENTS.open("a") as f:
                f.write(json.dumps({"time": now(), "node": n["id"], "from": old,
                                    "to": "dead",
                                    "reason": f"Planner: {MAX_RUNS} failed prover runs"},
                                   ensure_ascii=False) + "\n")
            print(f"  moved to graveyard: {n['id']}")
            buried += 1
    if buried:
        NODES.write_text(json.dumps(nodes, ensure_ascii=False, indent=2))
    else:
        print("  nothing to bury")

    print("== 3. Queue ==")
    status = {n["id"]: n["status"] for n in nodes}
    open_targets = [n for n in nodes if n.get("lean_goal") and n["status"] in OPEN]
    ready = [n for n in open_targets
             if all(status.get(d) == "checked" for d in n["depends_on"])]
    blocked = [n["id"] for n in open_targets if n not in ready]
    ready.sort(key=lambda n: (failures(n["id"]), n["id"]))
    for n in ready:
        print(f"  ready:   {n['id']} (failed runs so far: {failures(n['id'])})")
    for b in blocked:
        print(f"  blocked: {b} (waiting for its dependencies)")

    print("== 4. Prover ==")
    budget = json.loads(BUDGET.read_text()) if BUDGET.exists() else {}
    used = budget.get(today(), 0)
    for n in ready[:MAX_TARGETS]:
        if used >= DAILY_TOKENS:
            print(f"  daily budget reached ({used}/{DAILY_TOKENS} tokens). Stopping.")
            break
        print(f"  proving {n['id']} ... (tokens today: {used}/{DAILY_TOKENS})", flush=True)
        r = run("agents/prover.py", n["id"])
        m = re.search(r"Tokens used: (\d+)", r.stdout)
        used += int(m.group(1)) if m else 0
        budget[today()] = used
        BUDGET.write_text(json.dumps(budget, indent=2))
        result = [l for l in r.stdout.splitlines()
                  if l.startswith(("SUCCESS", "FAILED", "Proof compiled"))]
        print("    " + (result[-1] if result else "ERROR: " + r.stderr.strip()[-800:]))

    print("== 5. Data check ==")
    r = run("scripts/check_data.py")
    print("  " + "\n  ".join(r.stdout.strip().splitlines()))
    print(f"Done. Tokens used today: {used}/{DAILY_TOKENS}")


if __name__ == "__main__":
    main()