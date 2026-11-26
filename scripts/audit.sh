#!/usr/bin/env bash
# Audit: no sorry, no custom axioms, build passes, only standard axioms used.
set -euo pipefail
cd "$(dirname "$0")/../bsd_project"

echo "== Checking for sorry / custom axioms =="
if grep -rnwE "sorry|admit" BsdProject BsdProject.lean; then
  echo "FAIL: found sorry/admit"; exit 1
fi
if grep -rnE "^\s*axiom\s" BsdProject BsdProject.lean; then
  echo "FAIL: found a custom axiom"; exit 1
fi

echo "== Building =="
lake build

echo "== Axioms used by each theorem =="
tmp=".audit_tmp.lean"
trap 'rm -f "$tmp"' EXIT
{
  echo "import BsdProject"
  grep -rhoE "^(theorem|lemma) [A-Za-z0-9_'.]+" BsdProject \
    | awk '{print "#print axioms BsdProject." $2}'
} > "$tmp"

expected=$(grep -c "#print axioms" "$tmp" || true)
lake env lean "$tmp" | tee ../audit-report.txt
found=$(grep -cE "depends on axioms|does not depend on any axioms" ../audit-report.txt || true)

if [ "$expected" -eq 0 ] || [ "$expected" -ne "$found" ]; then
  echo "FAIL: expected $expected theorem results, got $found"; exit 1
fi

bad=$(grep -o '\[.*\]' ../audit-report.txt | tr -d '[] ' | tr ',' '\n' \
  | grep -vxE 'propext|Classical.choice|Quot.sound' | sort -u || true)
if [ -n "$bad" ]; then
  echo "FAIL: non-standard axioms used:"; echo "$bad"; exit 1
fi

echo "PASS: $found theorems checked, only standard axioms."
