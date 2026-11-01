# Memory guard, sourced by run_a3.sh and by the self-test (identical code). Thresholds are frozen defaults; A3_* env overrides exist ONLY for the self-test.
FLOOR_KB=${A3_FLOOR_KB:-512000}          # 500 MiB available RAM
SWAP_MIN_KB=${A3_SWAP_MIN_KB:-131072}    # swap "exhausted": under 128 MiB free
THRASH_PPS=${A3_THRASH_PPS:-25000}       # swap in+out pages per second ...
THRASH_N=${A3_THRASH_N:-30}              # ... for 30 consecutive 2 s samples (60 s) ...
THRASH_AVAIL_KB=${A3_THRASH_AVAIL_KB:-1048576}   # ... while MemAvailable < 1 GiB
desc() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do echo "$c"; desc "$c"; done; }
kill_tree() { local root=$1 pids; pids="$root $(desc $root)"; kill -TERM $pids 2>/dev/null; local i; for i in 1 2 3 4 5 6 7 8; do sleep 2; kill -0 $root 2>/dev/null || break; done; pids="$root $(desc $root) $pids"; kill -KILL $pids 2>/dev/null; return 0; }
swap_pages() { awk '/^pswpin /{a=$2} /^pswpout /{b=$2} END{print a+b}' /proc/vmstat; }
# guard_loop PID CSV MARKER_DIR : returns 0 if the process ended on its own, 97 if the guard terminated it
guard_loop() {
  local vpid=$1 csv=$2 mdir=$3 prev cur pps bad=0 avail swapfree rss pids list reason=""
  echo "epoch rss_kb_tree n_procs mem_available_kb swap_free_kb swap_pages_per_s thrash_streak" > $csv
  prev=$(swap_pages)
  while kill -0 $vpid 2>/dev/null; do
    pids="$vpid $(desc $vpid)"; list=$(echo $pids | tr ' ' ',')
    rss=$(ps -o rss= -p "$list" 2>/dev/null | awk '{s+=$1} END{print s+0}')
    avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo); swapfree=$(awk '/SwapFree/{print $2}' /proc/meminfo)
    cur=$(swap_pages); pps=$(( (cur - prev) / 2 )); prev=$cur
    if [ "$pps" -ge "$THRASH_PPS" ] && [ "$avail" -lt "$THRASH_AVAIL_KB" ]; then bad=$((bad+1)); else bad=0; fi
    echo "$(date +%s) $rss $(echo $pids | wc -w) $avail $swapfree $pps $bad" >> $csv
    if [ "$avail" -lt "$FLOOR_KB" ]; then reason="available RAM ${avail} kB below floor ${FLOOR_KB} kB"; fi
    if [ -z "$reason" ] && [ "$swapfree" -lt "$SWAP_MIN_KB" ]; then reason="swap exhausted: ${swapfree} kB free"; fi
    if [ -z "$reason" ] && [ "$bad" -ge "$THRASH_N" ]; then reason="sustained swap thrashing: ${pps} pages/s for ${bad} samples with ${avail} kB available"; fi
    if [ -n "$reason" ]; then
      { echo "RESOURCE_TERMINATED $(date -u +%FT%TZ)"; echo "reason: $reason"; echo "NOT a timing or routing result."; } > $mdir/RESOURCE_TERMINATED.txt
      kill_tree $vpid; return 97
    fi
    sleep 2
  done
  return 0
}
