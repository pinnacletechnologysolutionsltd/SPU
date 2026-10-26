#!/usr/bin/env bash
# ==============================================================================
# verify_repo.sh — Automated Repository Hygiene & Verification Gate
#
# Runs deterministic, token-free checks before commits or merges:
# 1. Root hygiene: checks for stray temporary files, waveforms, or scratch files.
# 2. Evidence gate: checks that NEWLY ADDED silicon-verification claims (lines
#    changed since HEAD) cite docs/hardware_evidence.md. Scoped to the diff, not
#    the whole tree, so pre-existing docs don't need to be cleared to pass.
# 3. Test regression: runs python3 run_all_tests.py and FAILS the gate on
#    any test failure (set SKIP_TESTS=1 to skip deliberately).
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ERRORS=0

echo "=== [1/3] Checking Root Directory Hygiene ==="
ROOT_CLUTTER=$(find . -maxdepth 1 -type f \( -name "tmp_*" -o -name "scratch_*" -o -name "*.bak" -o -name "*~" -o -name "*.vcd" \))
if [ -n "$ROOT_CLUTTER" ]; then
    echo "❌ ERROR: Root directory contains temporary/scratch files:"
    echo "$ROOT_CLUTTER"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Root directory is clean of scratch/temporary files."
fi

echo "=== [2/3] Checking Silicon Evidence Citation Integrity (new/changed lines only) ==="
# Only check markdown files with lines added since HEAD -- not the whole tree.
CLAIM_PAT="verified in silicon|silicon-verified|proven in silicon|silicon proof"
UNBACKED_HITS=0

CHANGED_MD_FILES=$(git diff --name-only HEAD -- '*.md' 2>/dev/null || true)

for file in $CHANGED_MD_FILES; do
    [ -f "$file" ] || continue  # skip deleted files
    # Skip the evidence ledger itself and historical handovers
    if [[ "$file" == "docs/hardware_evidence.md" ]] || [[ "$file" == *"SESSION_HANDOVER"* ]] || [[ "$file" == *"tranche_plan"* ]]; then
        continue
    fi

    # Only the lines this change actually added
    ADDED_LINES=$(git diff -U0 HEAD -- "$file" | grep -E '^\+[^+]' || true)
    if echo "$ADDED_LINES" | grep -inE "$CLAIM_PAT" > /dev/null 2>&1; then
        if ! grep -q "hardware_evidence.md" "$file"; then
            echo "❌ ERROR: $file adds a silicon claim but does not cite docs/hardware_evidence.md"
            UNBACKED_HITS=$((UNBACKED_HITS + 1))
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ "$UNBACKED_HITS" -gt 0 ]; then
    echo "⚠️  Found $UNBACKED_HITS changed files with potential unbacked silicon claims."
else
    echo "✅ Changed markdown files pass evidence citation check."
fi

echo "=== [3/3] Running Test Suite Regression Gate ==="
if [ "${SKIP_TESTS:-0}" = "1" ]; then
    echo "⏩ SKIP_TESTS=1 set; skipping test execution."
else
    # Check the suite's exit code explicitly. `set -e` did not catch this,
    # because run_all_tests.py had no sys.exit call and returned 0 even while
    # printing "Total FAIL: 2". Both ends are fixed as of 2026-09-05; this
    # half is the defence in depth, so a future regression in the runner's
    # exit code cannot silently disarm the gate a second time.
    if python3 run_all_tests.py; then
        echo "✅ Test suite passed."
    else
        echo "❌ ERROR: test suite reported failures (run_all_tests.py exit $?)."
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ "$ERRORS" -gt 0 ]; then
    echo "❌ Verification gate failed with $ERRORS error(s)."
    exit 1
fi

echo "✅ All verification checks completed successfully."
