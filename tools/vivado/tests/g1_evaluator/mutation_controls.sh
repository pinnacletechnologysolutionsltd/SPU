#!/usr/bin/env bash
# Mutation controls for the G1 evaluator: each mutant disables one E1/E2 protection; test_g1_evaluator.sh must then report BAD cases.
#   tools/vivado/tests/g1_evaluator/mutation_controls.sh SCRATCH_DIR      (repository root)
set -u
S="$1"; T=tools/vivado/tests/g1_evaluator; rm -rf "$S"; mkdir -p "$S"; fails=0
for m in M1_no_duplicate_block_check M2_no_block_row_crosscheck M3_no_row_without_block M4_E2_other_groups_ignored M5_unreadable_not_timing_fail; do
    python3 -I $T/mutate.py tools/vivado "$S/$m" $m || exit 2
    bad=$(bash $T/test_g1_evaluator.sh "$S/run_$m" "$S/$m/evaluate_g1_v2.sh" 2>&1 | grep -E ' BAD' | awk '{print $1}' | tr '\n' ' ')
    printf '%-34s %s  [%s]\n' $m "$([ -n "$bad" ] && echo DETECTED || echo MISSED)" "$bad"; [ -n "$bad" ] || fails=$((fails+1))
done
echo "MUTATION_CONTROLS $([ $fails -eq 0 ] && echo PASS || echo "FAIL ($fails missed)")"
[ $fails -eq 0 ]
