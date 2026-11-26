"""Run the whole team in a loop, so the site stays live:

  proposer (if the queue is empty) -> planner (refuter, graveyard, prover)
  -> computation (every few rounds) -> rebuild the website -> pause -> repeat

Stops by itself when today's token budget is used up. Stop it any time with Ctrl+C.

Usage:  python3 agents/run_forever.py
Settings: BSD_DAILY_TOKENS (default 200000), BSD_PAUSE seconds between rounds (default 60)
"""
import datetime, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data" / "nodes.json"
BUDGET = ROOT / "data" / "budget.json"
DAILY_TOKENS = int(os.environ.get("BSD_DAILY_TOKENS", "200000"))
PAUSE = int(os.environ.get("BSD_PAUSE", "60"))


def say(msg):
    print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}", flush=True)


def run(*cmd):
    return subprocess.run([sys.executable, *cmd], cwd=ROOT, capture_output=True, text=True)


def tokens_today():
    b = json.loads(BUDGET.read_text()) if BUDGET.exists() else {}
    return b.get(datetime.date.today().isoformat(), 0)


def add_tokens(n):
    b = json.loads(BUDGET.read_text()) if BUDGET.exists() else {}
    key = datetime.date.today().isoformat()
    b[key] = b.get(key, 0) + n
    BUDGET.write_text(json.dumps(b, indent=2))


def open_targets():
    nodes = json.loads(NODES.read_text())
    return [n for n in nodes if n.get("lean_goal") and n["status"] in ("conjecture", "in_progress")]


def main():
    rnd = 0
    say(f"Team started. Budget {DAILY_TOKENS} tokens/day. Ctrl+C to stop.")
    while True:
        rnd += 1
        if tokens_today() >= DAILY_TOKENS:
            say("Daily budget used up. Stopping until tomorrow.")
            break
        say(f"--- Round {rnd} ---")

        if not open_targets():
            say("Queue empty: asking the proposer for new claims")
            r = run("agents/proposer.py", "3")
            m = re.search(r"Tokens used: (\d+)", r.stdout)
            add_tokens(int(m.group(1)) if m else 0)
            for line in (r.stdout + r.stderr).strip().splitlines()[:6]:
                say("  proposer: " + line)

        say("Planner: refuter, graveyard, prover")
        r = run("agents/planner.py")
        for line in r.stdout.strip().splitlines():
            if any(k in line for k in ("passed", "REFUTED", "moved to", "SUCCESS", "FAILED",
                                       "ERROR", "STOP", "budget")):
                say("  " + line.strip())
        if r.returncode != 0:
            say("Planner stopped (see above). A human must look. Stopping.")
            break

        if rnd % 5 == 1:
            say("Computation: BSD formula for every curve")
            r = run("agents/compute.py")
            tail = r.stdout.strip().splitlines()
            say("  " + (tail[-2] if len(tail) >= 2 else (r.stderr.strip() or "no output")))

        run("scripts/build_site.py")
        say(f"Website rebuilt. Tokens today: {tokens_today()}/{DAILY_TOKENS}. "
            f"Next round in {PAUSE}s.")
        time.sleep(PAUSE)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("Stopped by you.")