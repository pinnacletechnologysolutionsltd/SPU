#!/usr/bin/env bash
# TRACKED PORT of build/vivado/g1e_prep/test_g1e.sh: fixtures from tools/vivado/tests/g1_evaluator/fixtures (compact, see PROVENANCE.txt).
# Offline qualification of the E1/E2 repair (evaluate_g1_v2.sh + timing_groups.py). Run from the repository root:
#   test_g1e.sh SCRATCH_DIR [EVALUATOR]        (EVALUATOR defaults to build/vivado/g1e_prep/evaluate_g1_v2.sh; mutation runs pass a weakened copy)
# Base: the REAL preserved G1 positive run (build/vivado/g1_pos_01 + detached_g1_pos_01), copied; negative controls mutate the COPY's timing summary
# with edit_ts.py. The original evidence is never written. Part B replays the real Step 7V NC3 reports and compares v1 and v2 dispositions.
set -u
S="$1"; EV="${2:-tools/vivado/evaluate_g1_v2.sh}"; E=tools/vivado/tests/g1_evaluator; V=build/vivado; FX=$E/fixtures
rm -rf "$S"; mkdir -p "$S"; fails=0
fident() { # fixture identity derived from the fixture's own run manifest (integrity semantics are exercised separately)
    m="$1/run_manifest.txt"; cat <<EOF
GIT_HEAD=$(awk '/^git_head /{print $2}' $m)
GIT_STATUS_SHA=$(awk '/^git_status_sha256 /{print $2}' $m)
GATE_SHA=$(sha256sum < tools/vivado/spu_vivado_flow.tcl | cut -d' ' -f1)
FILELIST_SHA=$(awk '/^filelist_sha256 /{print $2}' $m)
SOURCES_SHA=$(awk '/^source_sha256 /{print $2"  "$3}' $m | sort | sha256sum | cut -d' ' -f1)
G1_XDC=$(awk '/^arg -xdc /{print $3}' $m)
G1_XDC_SHA=$(awk '/^xdc_sha256 /{print $2}' $m)
NC_XDC=tools/vivado/tests/g1_evaluator/fixtures/nc_wrong_object.xdc
NC_XDC_SHA=$(sha256sum < tools/vivado/tests/g1_evaluator/fixtures/nc_wrong_object.xdc | cut -d' ' -f1)
NC_XDC_LINE=35
ATTEMPT_LIMIT=900
CUM_LIMIT=1800
CUM_DIRS="$2"
EOF
}

mk() { mkdir -p "$S/$1"; cp -r $FX/g1_pos/out "$S/$1/out"; cp -r $FX/g1_pos/det "$S/$1/det"; fident "$S/$1/out" "$S/$1/det" > "$S/$1/ident.env"; }
ed() { python3 -I $E/edit_ts.py "$S/$1/out/synth_timing_summary.rpt" "${@:2}"; }
run() { # name expected-dispositions [grep-must ...] [!grep-must-not ...]
    n=$1; want=$2; shift 2
    out=$(bash $EV pos "$S/$n/out" "$S/$n/det" "$S/$n/ident.env" 2>&1); printf '%s\n' "$out" > "$S/$n.eval.txt"
    got="$(printf '%s\n' "$out" | grep -E '^DISPOSITION (COVERAGE|TIMING|GATE-POSITIVE) ' | awk '{print $2"="$3}' | tr '\n' ' ')$(printf '%s\n' "$out" | grep '^VERDICT' | awk '{print $3}')"
    ok=1; [ "$got" = "$want" ] || ok=0; extra=""
    for p in "$@"; do case $p in '!'*) printf '%s\n' "$out" | grep -qF -- "${p#!}" && { ok=0; extra="$extra unexpected:'${p#!}'"; };;
                                  *) printf '%s\n' "$out" | grep -qF -- "$p" || { ok=0; extra="$extra missing:'$p'"; };; esac; done
    printf '%-30s %s  got: %s%s\n' "$n" "$([ $ok = 1 ] && echo OK || echo "BAD (want: $want)")" "$got" "$extra"
    [ $ok = 1 ] || fails=$((fails+1)); }
HOLD='sys_clk->guard_clk hold WHS -0.914 ns, THS -662.623 ns, 2205/8348 failing'
REMV='**async_default** sys_clk->guard_clk removal WHS -0.303 ns, THS -62.042 ns, 205/205 failing'
# ---- Part A: real G1 report and mutations of copies
mk a01_real_replay;             run a01_real_replay "COVERAGE=PASS TIMING=FAIL GATE-POSITIVE=PASS PROCEED" "$HOLD" "$REMV" "guard_clk guard_clk 14.667 0.000 0 27418" "sys_clk guard_clk 16.028 0.000 0 8348" "check_timing no_clock" "RECORD other/reverse"
mk a02_async_block_missing;     ed a02_async_block_missing drop_block '**async_default**' sys_clk guard_clk
                                run a02_async_block_missing "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "table row ('**async_default**', 'sys_clk', 'guard_clk') has no details block" "TIMING UNREADABLE"
mk a03_async_group_absent;      ed a03_async_group_absent drop_block '**async_default**' sys_clk guard_clk; ed a03_async_group_absent drop_row '**async_default**' sys_clk guard_clk
                                run a03_async_group_absent "COVERAGE=PASS TIMING=FAIL GATE-POSITIVE=PASS PROCEED" "$HOLD" "RECORD async_default sys_clk -> guard_clk (recovery/removal): absent" "!removal WHS"
mk a04_dup_pair_block;          ed a04_dup_pair_block dup_block - sys_clk guard_clk
                                run a04_dup_pair_block "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "duplicate details block ('-', 'sys_clk', 'guard_clk')"
mk a05_dup_async_block;         ed a05_dup_async_block dup_block '**async_default**' sys_clk guard_clk
                                run a05_dup_async_block "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "duplicate details block ('**async_default**', 'sys_clk', 'guard_clk')"
mk a06_contradictory_block;     ed a06_contradictory_block set_block_hold '**async_default**' sys_clk guard_clk 0 0.100 0.000
                                run a06_contradictory_block "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "contradicts table row"
mk a07_no_other_groups_section; ed a07_no_other_groups_section drop_section '| Other Path Groups Table'
                                run a07_no_other_groups_section "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "section '| Other Path Groups Table' found 0 times" "TIMING UNREADABLE"
mk a08_no_timing_details;       ed a08_no_timing_details drop_section '| Timing Details'
                                run a08_no_timing_details "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "section '| Timing Details' found 0 times"
mk a09_malformed_row;           ed a09_malformed_row break_row - sys_clk guard_clk
                                run a09_malformed_row "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "malformed row in Inter Clock Table"
mk a10_dup_table_row;           ed a10_dup_table_row dup_row '**async_default**' sys_clk guard_clk
                                run a10_dup_table_row "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "duplicate table row"
mk a11_removal_only;            ed a11_removal_only set_row_hold - sys_clk guard_clk 0.100 0.000 0; ed a11_removal_only set_block_hold - sys_clk guard_clk 0 0.100 0.000
                                run a11_removal_only "COVERAGE=PASS TIMING=FAIL GATE-POSITIVE=PASS PROCEED" "$REMV" "!hold WHS"
mk a12_no_violation;            ed a12_no_violation set_row_hold - sys_clk guard_clk 0.100 0.000 0; ed a12_no_violation set_block_hold - sys_clk guard_clk 0 0.100 0.000
                                ed a12_no_violation set_row_hold '**async_default**' sys_clk guard_clk 0.050 0.000 0; ed a12_no_violation set_block_hold '**async_default**' sys_clk guard_clk 0 0.050 0.000
                                run a12_no_violation "COVERAGE=PASS TIMING=NO-VIOLATION GATE-POSITIVE=PASS PROCEED" "!TIMING violations"
mk a13_pair_block_missing;      ed a13_pair_block_missing drop_block - sys_clk guard_clk
                                run a13_pair_block_missing "COVERAGE=FAIL TIMING=FAIL GATE-POSITIVE=PASS STOP" "table row ('-', 'sys_clk', 'guard_clk') has no details block"
# ---- Part B: Step 7V NC3 fixture — v2 must give the dispositions the frozen v1 gave on the same real reports
mkdir -p "$S/b01"; fident $FX/nc3/out $FX/nc3/det > "$S/b01/ident.env"
want="DISPOSITION INTEGRITY FAIL|DISPOSITION COVERAGE FAIL|DISPOSITION TIMING NO-VIOLATION (pre-placement estimate)|DISPOSITION GATE-POSITIVE FAIL|VERDICT pos STOP|"
got=$(bash $EV pos $FX/nc3/out $FX/nc3/det "$S/b01/ident.env" 2>&1 | grep -E '^(DISPOSITION|VERDICT)' | sed 's/ ([0-9]*)$//' | tr '\n' '|')
printf '%-30s %s  %s\n' b01_nc3_replay "$([ "$got" = "$want" ] && echo OK || echo "BAD (want: $want)")" "$got"; [ "$got" = "$want" ] || fails=$((fails+1))
if [ -e $V/g1_prep/evaluate_g1.sh ] && [ -d $V/step7v_nc3_01 ]; then   # optional: frozen v1 vs v2 on the FULL preserved reports
  d1=$(bash $V/g1_prep/evaluate_g1.sh pos $FX/nc3/out $FX/nc3/det "$S/b01/ident.env" 2>&1 | grep -E '^(DISPOSITION|VERDICT)' | sed 's/ ([0-9]*)$//' | tr '\n' '|')
  printf '%-30s %s\n' b02_v1_equals_v2 "$([ "$d1" = "$got" ] && echo OK || echo "BAD (v1: $d1)")"; [ "$d1" = "$got" ] || fails=$((fails+1))
fi
echo "G1E_TESTS $([ $fails -eq 0 ] && echo PASS || echo "FAIL ($fails)")"
[ $fails -eq 0 ]
