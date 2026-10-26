#!/usr/bin/bash
set -u ; set -o pipefail ; set -o noclobber           # no set -e: the finalization path below must always run
cd /home/john/Projects/hardware/SPU || exit 2
sha256sum -c research/qcg_0/p0/PINS.sha256 >/dev/null || exit 2                  # nothing is launched on any differing file
while IFS='|' read -r tool want; do
  [ "$("$tool" --version 2>&1 | head -1)" = "$want" ] || { echo "tool mismatch: $tool" >&2; exit 2; }
done < research/qcg_0/p0/TOOLS.manifest                                          # nothing is launched on any differing version
mkdir -p build/qcg_0 || exit 2
LEAF=build/qcg_0/run_01 ; mkdir "$LEAF" || exit 2                                # exclusive: refuses an existing leaf
{ date +%s.%N; git rev-parse HEAD; } > "$LEAF/provenance.txt" || exit 2          # informational only
/usr/bin/timeout 60 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304 -- \
  /usr/bin/python3 -B -I research/qcg_0/p0/run.py --out "$LEAF" >"$LEAF/stdout.log" 2>"$LEAF/stderr.log"
RC=$?
# ---- single finalization path: every step is attempted; nothing is inferred if any evidence write fails ----
PRC=0 ; PINS_AFTER=$(sha256sum -c research/qcg_0/p0/PINS.sha256 2>&1 | head -c 1024) || true
sha256sum -c research/qcg_0/p0/PINS.sha256 >/dev/null 2>&1 || PRC=1               # post-run pin check, always attempted
USED=$(du -sb "$LEAF" 2>/dev/null | cut -f1) ; USED=${USED:-99999999}
CAUSE=""
if [ $((USED + 4096)) -gt 10485760 ] || [ "$RC" -eq 90 ] || [ "$RC" -eq 153 ] || [ -e "$LEAF/CAP_BREACH" ]; then CAUSE=OUTPUT_CAP ; fi
# 1. all REQUIRED metadata first; no marker has been chosen or written yet
W=0
echo "$RC" > "$LEAF/exit.code" || W=1
{ echo "pins_after_rc=$PRC"; printf '%s\n' "$PINS_AFTER" | head -c 1024; } > "$LEAF/pins_after.txt" || W=1   # bounded: <= 1 KiB + header
if [ -n "$CAUSE" ]; then : > "$LEAF/$CAUSE" || W=1 ; fi
# 2. only now choose the marker; any metadata failure forces FAILED and can never leave COMPLETE or TIMEOUT
if [ "$W" -ne 0 ]; then MARK=FAILED ; : > "$LEAF/FINALIZE_FAILED" 2>/dev/null || true
elif [ -n "$CAUSE" ]; then MARK=FAILED
elif [ "$RC" -eq 0 ] && [ -f "$LEAF/RUNNER_DONE" ]; then MARK=COMPLETE
elif [ "$RC" -eq 124 ]; then MARK=TIMEOUT
else MARK=FAILED; fi
MW=0 ; : > "$LEAF/$MARK" || MW=1
N=0 ; for m in COMPLETE FAILED TIMEOUT ; do if [ -e "$LEAF/$m" ]; then N=$((N+1)); fi ; done
if [ "$N" -eq 0 ]; then echo "RESULT_UNAVAILABLE: no terminal marker persisted" >&2 ; exit 4 ; fi   # nothing is inferred
if [ "$W" -ne 0 ] || [ "$MW" -ne 0 ] || [ "$N" -ne 1 ]; then echo "FINALIZE_FAILED write=$W marker_write=$MW markers=$N" >&2 ; exit 3 ; fi
case "$MARK" in COMPLETE) exit 0;; TIMEOUT) exit 11;; *) exit 10;; esac
