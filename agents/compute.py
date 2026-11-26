"""Computation agent: uses PARI/GP to compute, for every curve, both sides of
the full BSD formula and check that they agree numerically.

  L^(r)(E,1)/r!  =  Omega * Reg * prod(c_p) * |Sha|  /  |E_tors|^2

PARI's ellanalyticrank(E) returns [r, L^(r)(E,1)] (the r-th derivative), so we
divide by r! to get the leading Taylor coefficient. PARI's ellbsd(E) gives
Omega * prod(c_p) / |E_tors|^2, so the "analytic order of Sha" is
  sha_an = (L^(r)(E,1)/r!) / (ellbsd(E) * Reg).
BSD predicts sha_an is a perfect square integer, and that rank = analytic rank.

These are NUMERICAL results: evidence only, never marked 'checked'.
"""
import datetime, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURVES = ROOT / "data" / "curves.json"
OUT = ROOT / "data" / "computations.json"

GP_SCRIPT = """
E = ellminimalmodel(ellinit({ainvs}));
ar = ellanalyticrank(E); r = ar[1]; Lr = ar[2] / r!;
rk = ellrank(E); lo = rk[1]; hi = rk[2]; P = rk[4];
if (#P > 0, P = ellsaturation(E, P, 100));
R = if (#P == 0, 1, matdet(ellheightmatrix(E, P)));
T = elltors(E)[1];
c = ellglobalred(E)[3];
b = ellbsd(E);
sha = Lr / (b * R);
print(r, ";", lo, ";", hi, ";", #P, ";", T, ";", c, ";", R, ";", Lr, ";", sha);
"""


def num(x):
    return float(x.replace(" ", ""))


def run_gp(ainvs):
    r = subprocess.run(["gp", "-q", "-f"], input=GP_SCRIPT.format(ainvs=ainvs),
                       capture_output=True, text=True, timeout=600)
    lines = [l for l in r.stdout.splitlines() if l.count(";") == 8]
    if not lines:
        raise RuntimeError((r.stdout + r.stderr).strip()[-600:])
    f = lines[-1].split(";")
    return {"analytic_rank": int(f[0]), "rank_lower": int(f[1]),
            "rank_upper": int(f[2]), "generators": int(f[3]),
            "torsion": int(f[4]), "tamagawa": int(f[5]),
            "regulator": num(f[6]), "leading_term": num(f[7]),
            "sha_an": num(f[8])}


def verdict(d, listed_rank):
    issues = []
    if d["rank_lower"] != d["rank_upper"]:
        issues.append(f"rank only bounded: {d['rank_lower']}..{d['rank_upper']}")
    elif d["rank_lower"] != d["analytic_rank"]:
        issues.append("CONFLICT: rank != analytic rank (bug, or huge news)")
    if d["generators"] != d["rank_lower"]:
        issues.append("not enough generators for the regulator")
    if listed_rank is not None and listed_rank != d["rank_lower"]:
        issues.append(f"rank differs from curves.json ({listed_rank})")
    s = round(d["sha_an"])
    if abs(d["sha_an"] - s) > 1e-6 or s < 1 or int(s ** 0.5) ** 2 != s:
        issues.append(f"sha_an = {d['sha_an']:.8f} is not a perfect square")
    return ("consistent" if not issues else "inconclusive"), issues


def main():
    version = subprocess.run(["gp", "--version-short"], capture_output=True,
                             text=True).stdout.strip()
    curves = json.loads(CURVES.read_text())
    results = {}
    print(f"PARI/GP {version}\n")
    print(f"{'curve':16} {'rank':>4} {'an.rk':>5} {'tors':>4} {'tam':>4} "
          f"{'regulator':>12} {'Sha_an':>10}  verdict")
    for c in curves:
        try:
            d = run_gp(c["ainvs"])
        except Exception as e:
            print(f"{c['label']:16} ERROR: {e}")
            continue
        status, issues = verdict(d, c.get("rank"))
        d.update(status=status, issues=issues, pari=version,
                 time=datetime.datetime.now().isoformat(timespec="seconds"))
        results[c["label"]] = d
        c["bsd_numeric"] = status
        c["sha_an"] = round(d["sha_an"])
        print(f"{c['label']:16} {d['rank_lower']:>4} {d['analytic_rank']:>5} "
              f"{d['torsion']:>4} {d['tamagawa']:>4} {d['regulator']:>12.6f} "
              f"{d['sha_an']:>10.6f}  {status}")
        for i in issues:
            print(f"{'':16} - {i}")

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    CURVES.write_text(json.dumps(curves, ensure_ascii=False, indent=2))
    ok = sum(r["status"] == "consistent" for r in results.values())
    print(f"\n{ok}/{len(curves)} curves numerically consistent with full BSD.")
    print("Saved to data/computations.json (numerical evidence, not proofs).")


if __name__ == "__main__":
    main()