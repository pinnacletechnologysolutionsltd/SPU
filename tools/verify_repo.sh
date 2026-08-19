#!/usr/bin/env bash
# ==============================================================================
# verify_repo.sh — Automated Repository Hygiene & Verification Gate
#
# Runs deterministic, token-free checks before commits or merges:
# 1. Root hygiene: checks for stray temporary files, waveforms, or scratch files.
# 2. Evidence gate: checks that claims of silicon verification cite docs/hardware_evidence.md.
# 3. Test regression: optionally runs python3 run_all_tests.py.
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ERRORS=0

echo "=== [1/3] Checking Root Directory Hygiene ==="
ROOT_CLUTTER=$(find . -maxdepth 1 -type f \( -name "tmp_*" -o -name "scratch_*" -o -name "*.bak" -o -name "*~" \))
if [ -n "$ROOT_CLUTTER" ]; then
    echo "❌ ERROR: Root directory contains temporary/scratch files:"
    echo "$ROOT_CLUTTER"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Root directory is clean of scratch/temporary files."
fi

echo "=== [2/3] Checking Silicon Evidence Citation Integrity ==="
# Check modified or staged markdown files for unbacked claims
CLAIM_PAT="verified in silicon|silicon-verified|proven in silicon|silicon proof"
UNBACKED_HITS=0

for file in $(find docs knowledge spu_strategy -name "*.md" 2>/dev/null); do
    # Skip the evidence ledger itself and historical handovers
    if [[ "$file" == "docs/hardware_evidence.md" ]] || [[ "$file" == *"SESSION_HANDOVER"* ]] || [[ "$file" == *"tranche_plan"* ]]; then
        continue
    fi
    
    # If a file asserts silicon verification, verify it references hardware_evidence.md
    if grep -inE "$CLAIM_PAT" "$file" > /dev/null 2>&1; then
        if ! grep -q "hardware_evidence.md" "$file"; then
            echo "⚠️  WARNING: $file makes silicon claims but does not cite docs/hardware_evidence.md"
            UNBACKED_HITS=$((UNBACKED_HITS + 1))
        fi
    fi
done

if [ "$UNBACKED_HITS" -gt 0 ]; then
    echo "⚠️  Found $UNBACKED_HITS files with potential unbacked silicon claims."
else
    echo "✅ Markdown files pass evidence citation check."
fi

echo "=== [3/3] Running Test Suite Regression Gate ==="
if [ "${SKIP_TESTS:-0}" = "1" ]; then
    echo "⏩ SKIP_TESTS=1 set; skipping test execution."
else
    python3 run_all_tests.py
fi

if [ "$ERRORS" -gt 0 ]; then
    echo "❌ Verification gate failed with $ERRORS error(s)."
    exit 1
fi

echo "✅ All verification checks completed successfully."
