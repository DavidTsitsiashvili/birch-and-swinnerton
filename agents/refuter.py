"""Refuter agent: independently tests every claim that has a `check`,
using exact rational arithmetic on the curve data.

- An open claim that fails its check is marked `refuted`.
- A `checked` (Lean-proved) claim that fails is a CONFLICT: the Lean
  statement probably does not mean what the claim says. Never auto-changed.
"""
import datetime, json, math
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data" / "nodes.json"
CURVES = ROOT / "data" / "curves.json"
EVENTS = ROOT / "data" / "events.jsonl"


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def disc(a):
    a1, a2, a3, a4, a6 = map(F, a)
    b2 = a1 * a1 + 4 * a2
    b4 = 2 * a4 + a1 * a3
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    return -b2 * b2 * b8 - 8 * b4 ** 3 - 27 * b6 * b6 + 9 * b2 * b4 * b6


def on_curve(a, x, y):
    a1, a2, a3, a4, a6 = map(F, a)
    x, y = F(x), F(y)
    return y * y + a1 * x * y + a3 * y == x ** 3 + a2 * x * x + a4 * x + a6


def integral_points(a, bound=100):
    """All integral points with |x| <= bound (solves the quadratic in y)."""
    a1, a2, a3, a4, a6 = a
    pts = []
    for x in range(-bound, bound + 1):
        rhs = x ** 3 + a2 * x * x + a4 * x + a6
        b = a1 * x + a3
        d = b * b + 4 * rhs          # y = (-b ± sqrt(d)) / 2
        if d < 0:
            continue
        r = math.isqrt(d)
        if r * r != d:
            continue
        for s in {r, -r}:
            if (s - b) % 2 == 0:
                pts.append((x, (s - b) // 2))
    return sorted(set(pts))


def run_check(chk, curves):
    a = curves[chk["curve"]]["ainvs"]
    t = chk["type"]
    if t == "disc":
        got = disc(a)
        return got == chk["value"], f"computed discriminant {got}, claimed {chk['value']}"
    if t == "nonzero_disc":
        got = disc(a)
        return got != 0, f"computed discriminant {got}"
    if t == "on_curve":
        x, y = chk["point"]
        ok = on_curve(a, x, y)
        return ok, f"({x}, {y}) {'is' if ok else 'is NOT'} on the curve"
    return None, f"unknown check type {t}"


def main():
    nodes = json.loads(NODES.read_text())
    curves = {c["label"]: c for c in json.loads(CURVES.read_text())}
    events, conflicts, refuted, passed = [], [], [], 0

    for n in nodes:
        chk = n.get("check")
        if not chk or n["status"] in ("refuted", "dead"):
            continue
        ok, detail = run_check(chk, curves)
        if ok:
            passed += 1
            print(f"  pass      {n['id']}: {detail}")
        elif ok is False and n["status"] == "checked":
            conflicts.append(n["id"])
            print(f"  CONFLICT  {n['id']}: Lean says checked, but {detail}")
        elif ok is False:
            events.append({"time": now(), "node": n["id"], "from": n["status"],
                           "to": "refuted", "reason": f"Refuter: {detail}"})
            n.update(status="refuted", updated_at=now(),
                     evidence=f"refuter: {detail}")
            refuted.append(n["id"])
            print(f"  REFUTED   {n['id']}: {detail}")
        else:
            print(f"  skipped   {n['id']}: {detail}")

    print("\nCurve sanity (integral points with |x| <= 100):")
    for label, c in curves.items():
        d = disc(c["ainvs"])
        pts = integral_points(c["ainvs"])
        print(f"  {label}: discriminant {d}, rank {c['rank']}, "
              f"{len(pts)} integral points, e.g. {pts[:4]}")
        if d == 0:
            conflicts.append(label)
            print(f"  CONFLICT  {label}: discriminant is 0, not an elliptic curve")

    if events:
        NODES.write_text(json.dumps(nodes, ensure_ascii=False, indent=2))
        with EVENTS.open("a") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"\n{passed} passed, {len(refuted)} refuted, {len(conflicts)} conflicts.")
    if conflicts:
        print("CONFLICTS need a human:", ", ".join(conflicts))
        raise SystemExit(1)


if __name__ == "__main__":
    main()