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
lake env lean BsdProject/Axioms.lean | tee ../audit-report.txt

bad=$(grep -o '\[.*\]' ../audit-report.txt | tr -d '[] ' | tr ',' '\n' \
  | grep -vxE 'propext|Classical.choice|Quot.sound' | sort -u || true)
if [ -n "$bad" ]; then
  echo "FAIL: non-standard axioms used:"; echo "$bad"; exit 1
fi

echo "PASS: all theorems checked, only standard axioms."