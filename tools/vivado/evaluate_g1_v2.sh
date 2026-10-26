#!/usr/bin/env bash
# G1 evaluator v2 (E1/E2 repair of the frozen v1 65527dde…): all timing groups incl. async_default and Other Path Groups. Read-only; run from the repository root.
#   evaluate_g1.sh pos|nc OUT_DIR DETACHED_DIR IDENTITY_ENV
# pos: three separate dispositions — COVERAGE (structural timing coverage), TIMING (violations; pre-placement estimate), GATE (strict-gate
#      positive control: COMPLETE). Campaign may proceed to nc only on INTEGRITY + COVERAGE + GATE PASS; a TIMING FAIL is recorded, not hidden.
# nc:  wrong generated-clock target object; gate must fail for that reason, attributed to genuine Vivado lines at the frozen XDC line.
set -u
c="$1"; O="$2"; D="$3"; . "$4"
fi=0; fc=0; ft=0; fg=0; fn=0
ck() { # section name got want
    if [ "$3" = "$4" ]; then echo "CHECK OK   [$1] $2"; else echo "CHECK FAIL [$1] $2 (got '$3', want '$4')"
        case $1 in INTEGRITY) fi=$((fi+1));; COVERAGE) fc=$((fc+1));; GATE) fg=$((fg+1));; NC) fn=$((fn+1));; esac; fi; }
dur() { python3 -I -c 'import json,sys;print(json.load(open(sys.argv[1]))["duration_seconds"])' "$1" 2>/dev/null || echo NA; }
num_ge() { python3 -I -c 'import sys
try: print("yes" if float(sys.argv[1]) >= float(sys.argv[2]) else "no")
except ValueError: print("no")' "$1" "$2"; }
case "$c" in pos) XDC=$G1_XDC; XSHA=$G1_XDC_SHA; WANT=COMPLETE; RC=0;; nc) XDC=$NC_XDC; XSHA=$NC_XDC_SHA; WANT=FAILED; RC=1;; *) echo "usage"; exit 2;; esac
# ---------------- INTEGRITY
ck INTEGRITY "runner terminal markers" "$(for m in COMPLETE FAILED TIMEOUT; do [ -e $D/$m ] && printf '%s ' $m; done)" "$WANT "
ck INTEGRITY "flow terminal markers" "$(for m in COMPLETE FAILED; do [ -e $O/$m ] && printf '%s ' $m; done)" "$WANT "
ck INTEGRITY "exit status" "$(cat $D/exit_status 2>/dev/null)" "$RC"
d=$(dur $D/result.json); echo "INFO duration_seconds $d"
ck INTEGRITY "duration within $ATTEMPT_LIMIT s" "$([ "$d" != NA ] && [ "$d" -le "$ATTEMPT_LIMIT" ] && echo yes || echo no)" "yes"
cum=0; for x in $CUM_DIRS; do [ -e $x/result.json ] && cum=$((cum + $(dur $x/result.json))); done; echo "INFO cumulative_seconds $cum"
ck INTEGRITY "cumulative within $CUM_LIMIT s" "$([ $cum -le "$CUM_LIMIT" ] && echo yes || echo no)" "yes"
m=$O/run_manifest.txt
ck INTEGRITY "git_head" "$(awk '/^git_head /{print $2}' $m)" "$GIT_HEAD"
ck INTEGRITY "git_status_sha256" "$(awk '/^git_status_sha256 /{print $2}' $m)" "$GIT_STATUS_SHA"
ck INTEGRITY "gate source sha256" "$(sha256sum < tools/vivado/spu_vivado_flow.tcl | cut -d' ' -f1)" "$GATE_SHA"
ck INTEGRITY "strict" "$(awk '/^arg -strict /{print $3}' $m)" "1"
ck INTEGRITY "expect_clock arguments" "$(awk '/^arg -expect_clock /{print $3}' $m | sort | tr '\n' ' ')" "guard_clk:40.000 sys_clk:20.000 "
ck INTEGRITY "xdc argument" "$(awk '/^arg -xdc /{print $3}' $m)" "$XDC"
ck INTEGRITY "xdc sha256" "$(awk '/^xdc_sha256 /{print $2}' $m)" "$XSHA"
ck INTEGRITY "filelist sha256" "$(awk '/^filelist_sha256 /{print $2}' $m)" "$FILELIST_SHA"
ck INTEGRITY "source set sha256" "$(awk '/^source_sha256 /{print $2"  "$3}' $m | sort | sha256sum | cut -d' ' -f1)" "$SOURCES_SHA"
L=$O/vivado.log; MK=SPU_GATE_SCOPE_BEGIN
ck INTEGRITY "scope marker exactly once, column 0, literal nowhere else" "$(grep -cx "$MK" $L)/$(grep -c "$MK" $L)" "1/1"
mkn=$(grep -nx "$MK" $L | head -1 | cut -d: -f1); [ -n "$mkn" ] || mkn=999999999
AFTER=$(tail -n +$((mkn + 1)) $L 2>/dev/null)
R=$(tail -n +2 $O/FAILED 2>/dev/null | sed 's/^  //')
CT=$O/synth_check_timing.rpt
ctn() { grep -m1 -oE "checking $1 \(([0-9]+)\)" $CT | grep -oE '[0-9]+' || echo NA; }
if [ "$c" = pos ]; then
  # ---------------- GATE (strict-gate positive control)
  ck GATE "no FAILED file / no gate reasons" "$([ -e $O/FAILED ] && echo present || echo absent)" "absent"
  [ -n "$R" ] && { echo "INFO gate reasons:"; printf '%s\n' "$R" | sed 's/^/       /'; }
  # ---------------- COVERAGE
  for k in no_clock unconstrained_internal_endpoints generated_clocks multiple_clock pulse_width_clock loops; do ck COVERAGE "check_timing $k" "$(ctn $k)" "0"; done
  echo "INFO check_timing no_input_delay $(ctn no_input_delay), no_output_delay $(ctn no_output_delay) (I/O policy deferred to G3; baseline 4/1)"
  CL=$O/synth_clocks.rpt
  grow=$(grep -E '^guard_clk[[:space:]]' $CL | head -1); echo "INFO clocks row: $grow"
  ck COVERAGE "guard_clk period 40.000, waveform {0.000 20.000}" "$(printf '%s\n' "$grow" | awk '{print $2, $3, $4}')" "40.000 {0.000 20.000}"
  ck COVERAGE "guard_clk attributes include G (generated)" "$(printf '%s\n' "$grow" | awk '{print $5}' | grep -c G)" "1"
  ck COVERAGE "guard_clk source is guard_clk_div_reg/Q" "$(printf '%s\n' "$grow" | grep -c 'guard_clk_div_reg/Q')" "1"
  ck COVERAGE "generated clocks in clock table = 1" "$(awk '/^Clock[[:space:]]+Period/{t=1;next} t && NF>=5 && $1!~/^-+$/ && $5~/G/{n++} END{print n+0}' $CL)" "1"
  ck COVERAGE "sys_clk still 20.000 {0.000 10.000}" "$(grep -E '^sys_clk[[:space:]]' $CL | head -1 | awk '{print $2, $3, $4}')" "20.000 {0.000 10.000}"
  ck COVERAGE "no unconstrained clocks in clock networks" "$(awk '/^Unconstrained Clocks$/{u=1;next} /^[A-Z][a-z]+ Clocks$/{u=0} u && /^Clock /{n++} END{print n+0}' $O/synth_clock_networks.rpt)" "0"
  echo "INFO clock networks guard_clk: $(grep -E '^Clock guard_clk ' $O/synth_clock_networks.rpt | head -1)"
  # E1/E2 (g1e): every timing group of the summary, tables cross-checked against Timing Details blocks (timing_groups.py, fail-closed).
  TS=$O/synth_timing_summary.rpt
  TG=$(python3 -I "$(dirname "$0")/timing_groups.py" $TS 2>&1)
  echo "INFO timing groups (group from to | WNS TNS fail total | WHS THS fail total):"; printf '%s\n' "$TG" | grep -E '^ROW ' | sed 's/^ROW /       /'
  terr=$(printf '%s\n' "$TG" | grep -E '^ERR ' | sed 's/^ERR //'); [ -n "$terr" ] && { echo "INFO timing-structure errors:"; printf '%s\n' "$terr" | sed 's/^/       /'; }
  ck COVERAGE "timing summary structure consistent (sections, rows, unique groups, blocks agree with rows)" "$(printf '%s\n' "$terr" | grep -c .)" "0"
  row() { printf '%s\n' "$TG" | awk -v g="$1" -v f="$2" -v t="$3" '$1=="ROW" && $2==g && $3==f && $4==t'; }
  gtot=$(row - guard_clk guard_clk | awk '{print $8}')
  ck COVERAGE "guard_clk timed setup endpoints >= 6000" "$(num_ge "${gtot:-NA}" 6000)" "yes"
  ftot=$(row - sys_clk guard_clk | awk '{print $8}')
  ck COVERAGE "sys_clk -> guard_clk clock-pair group with >= 1 endpoint" "$(num_ge "${ftot:-NA}" 1)" "yes"
  ck COVERAGE "exactly one clock-pair details block sys_clk -> guard_clk" "$(printf '%s\n' "$TG" | awk '$1=="BLOCK" && $2=="-" && $3=="sys_clk" && $4=="guard_clk"' | wc -l)" "1"
  arow=$(row '**async_default**' sys_clk guard_clk); echo "RECORD async_default sys_clk -> guard_clk (recovery/removal): ${arow:-absent}"
  rev=$(printf '%s\n' "$TG" | awk '$1=="ROW" && $2=="-" && $3!=$4 && !($3=="sys_clk" && $4=="guard_clk")' | sed 's/^ROW //')
  if [ -n "$rev" ]; then echo "RECORD other/reverse inter-clock rows (Amendment A: investigate, not auto-fail):"; printf '%s\n' "$rev" | sed 's/^/       /'; else echo "RECORD no reverse or other inter-clock rows"; fi
  t17=$(awk -F'|' '$2 ~ /^ *TIMING-17 *$/ {gsub(/ /,"",$5); print $5}' $O/synth_methodology.rpt); ck COVERAGE "methodology TIMING-17 count" "${t17:-0}" "0"
  # ---------------- TIMING (separate disposition; pre-placement estimate). Every group, including Other Path Groups (E2).
  if [ -n "$terr" ]; then ft=1; echo "TIMING UNREADABLE: timing summary structure errors above (fail closed)"; fi
  viol=$(printf '%s\n' "$TG" | awk '$1=="ROW" { s=($2=="**async_default**")?"recovery":"setup"; h=($2=="**async_default**")?"removal":"hold";
      if (($5+0<0 && $5!="NA") || $7+0>0) printf "%s %s->%s %s WNS %s ns, %s/%s failing\n", $2, $3, $4, s, $5, $7, $8;
      if (($9+0<0 && $9!="NA") || $11+0>0) printf "%s %s->%s %s WHS %s ns, THS %s ns, %s/%s failing\n", $2, $3, $4, h, $9, $10, $11, $12 }')
  if [ -n "$viol" ]; then ft=1; echo "TIMING violations (recorded as TIMING FAIL, pre-placement estimate):"; printf '%s\n' "$viol" | sed 's/^/       /'; fi
  # ---------------- RECORDED (not gated)
  echo "RECORD methodology rows: $(awk -F'|' '$2 ~ /[A-Z]+-[0-9]+/ {gsub(/^ +| +$/,"",$2); gsub(/ /,"",$5); printf "%s=%s ", $2, $5}' $O/synth_methodology.rpt)"
  echo "RECORD DRC rows: $(awk -F'|' '$2 ~ /[A-Z]+-[0-9]+/ {gsub(/^ +| +$/,"",$2); gsub(/ /,"",$5); printf "%s=%s ", $2, $5}' $O/synth_drc.rpt)"
  echo "RECORD utilization: $(grep -E '^\| (Slice LUTs\*?|Slice Registers|DSPs|Block RAM Tile) ' $O/synth_utilization.rpt | awk -F'|' '{gsub(/ +/," ",$2); gsub(/ /,"",$3); printf "%s=%s;", $2, $3}')"
  echo "RECORD CDC: $(grep -m3 -iE 'Safely|Unsafe|Unknown|No CDC' $O/synth_cdc.rpt | tr -s ' ' | tr '\n' ' ')"
  [ $fi -eq 0 ] && echo "DISPOSITION INTEGRITY PASS" || echo "DISPOSITION INTEGRITY FAIL ($fi)"
  [ $fc -eq 0 ] && echo "DISPOSITION COVERAGE PASS" || echo "DISPOSITION COVERAGE FAIL ($fc)"
  [ $ft -eq 0 ] && echo "DISPOSITION TIMING NO-VIOLATION (pre-placement estimate)" || echo "DISPOSITION TIMING FAIL (recorded)"
  [ $fg -eq 0 ] && echo "DISPOSITION GATE-POSITIVE PASS" || echo "DISPOSITION GATE-POSITIVE FAIL ($fg)"
  [ $((fi + fc + fg)) -eq 0 ] && echo "VERDICT pos PROCEED" || echo "VERDICT pos STOP"
  [ $((fi + fc + fg)) -eq 0 ]
else
  # ---------------- NC: wrong generated-clock target object at the frozen XDC line
  ABS="$(pwd)/$XDC:$NC_XDC_LINE"
  echo "INFO reasons:"; printf '%s\n' "$R" | sed 's/^/       /'
  ck NC "each reason unique; no scope-marker reason" "$(printf '%s\n' "$R" | sort | uniq -d | wc -l)/$(printf '%s\n' "$R" | grep -c 'log scope marker')" "0/0"
  DIAG=$(printf '%s\n' "$AFTER" | grep -E '^(CRITICAL WARNING|WARNING|ERROR): \[[A-Za-z][A-Za-z0-9_ ]* [0-9]+-[0-9]+\] ' | grep -F "[$ABS]")
  echo "INFO genuine Vivado diagnostics at frozen line (after marker):"; printf '%s\n' "$DIAG" | sed 's/^/       /'
  ck NC "attribution: >= 1 genuine CRITICAL WARNING at frozen line" "$([ "$(printf '%s\n' "$DIAG" | grep -c '^CRITICAL WARNING: ')" -ge 1 ] && echo yes || echo no)" "yes"
  ck NC "attribution: no diagnostics at other lines of the control XDC" "$(printf '%s\n' "$AFTER" | grep -E '^(CRITICAL WARNING|WARNING|ERROR): \[' | grep -F "$(pwd)/$XDC:" | grep -vcF "[$ABS]")" "0"
  CR=$(printf '%s\n' "$R" | grep -E '^constraint resolved to nothing')
  ck NC "detection: >= 1 constraint-resolution reason" "$([ -n "$CR" ] && echo yes || echo no)" "yes"
  ck NC "detection: every constraint-resolution reason quotes a genuine diagnostic at the frozen line" "$(printf '%s\n' "$CR" | grep -v '^$' | while IFS= read -r r; do q=${r#*: }; printf '%s\n' "$DIAG" | grep -qxF "$q" || echo bad; done | grep -c bad)" "0"
  ck NC "expected-clock reason for guard_clk" "$(printf '%s\n' "$R" | grep -cxF "expected clock 'guard_clk' does not exist (missing or unresolved create_clock)")" "1"
  ck NC "other reasons exactly the baseline timing pair" "$(printf '%s\n' "$R" | grep -v '^constraint resolved to nothing' | grep -vxF "expected clock 'guard_clk' does not exist (missing or unresolved create_clock)" | sort | tr '\n' '|')" "check_timing: no_clock = 8172|check_timing: unconstrained_internal_endpoints = 28651|"
  # Classify a missed detection only when the scope is valid; otherwise the marker failure above is the cause.
  miss=""; [ "$(grep -cx "$MK" $L)" = 1 ] || CR=marker-invalid
  if [ -z "$CR" ] && printf '%s\n' "$DIAG" | grep -q '^CRITICAL WARNING: '; then miss=" — GATE MISS (genuine CRITICAL WARNING not detected; stop, no repair)"; fi
  if [ -z "$CR" ] && ! printf '%s\n' "$DIAG" | grep -q '^CRITICAL WARNING: '; then miss=" — no CRITICAL WARNING at the frozen line"; fi
  [ $((fi + fn)) -eq 0 ] && echo "VERDICT nc PASS" || echo "VERDICT nc FAIL ($((fi + fn)) failed checks)$miss"
  [ $((fi + fn)) -eq 0 ]
fi
