#!/usr/bin/env bash
# Run exactly one frozen strategy comparison and preserve its terminal state.
set -u
if [[ $# -ne 2 ]]; then echo "usage: $0 PLAN_JSON NEW_EVIDENCE_DIR" >&2; exit 2; fi
plan=$1
evidence=$2
if [[ -e "$evidence" ]]; then echo "refusing existing evidence directory: $evidence" >&2; exit 2; fi
mkdir -p "$evidence" || exit 2
started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
command="timeout --kill-after=5s 60s python3 software/experiments/surd_register_strategy_compare_run.py --run $plan $evidence"
timeout --kill-after=5s 60s python3 software/experiments/surd_register_strategy_compare_run.py --run "$plan" "$evidence" \
    >"$evidence/stdout.log" 2>"$evidence/stderr.log"
rc=$?
finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)
status=FAILED
if [[ $rc -eq 0 ]]; then status=COMPLETE; fi
if [[ $rc -eq 124 ]]; then status=TIMEOUT; fi
tmp="$evidence/terminal.txt.tmp"
{
    printf 'format=SPU_SURD_STRATEGY_TERMINAL_V1\n'
    printf 'terminal_status=%s\nexit_code=%s\n' "$status" "$rc"
    printf 'started_utc=%s\nfinished_utc=%s\ncommand=%s\n' "$started" "$finished" "$command"
} >"$tmp" && mv "$tmp" "$evidence/terminal.txt"
exit "$rc"
