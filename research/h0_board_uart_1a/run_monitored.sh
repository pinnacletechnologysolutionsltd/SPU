#!/usr/bin/env bash
# Future separately authorized run only; must be called by detached runner.
set -uo pipefail
WT=$(realpath -e -- "$1") || exit 98
BUILD=$(realpath -e -- "$WT/build") || exit 98
OUT=$(realpath -m -- "$2") || exit 98
MON=$(realpath -m -- "$3") || exit 98
[[ "$OUT" == "$BUILD"/* && "$MON" == "$BUILD"/* && ! -e "$OUT" && ! -e "$MON" ]] || exit 98
[[ "$OUT" != "$MON" && "$OUT" != "$MON"/* && "$MON" != "$OUT"/* ]] || exit 98
mkdir -p "$MON" || exit 98
{ date -u +%FT%TZ; grep -E 'MemTotal|MemAvailable|SwapTotal|SwapFree' /proc/meminfo; } > "$MON/memory_before.txt"
av=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
if (( av < 5242880 )); then echo 'HOLD: MemAvailable below 5 GiB; no waiver authorized' > "$MON/HOLD_MEMORY"; exit 97; fi
source /home/john/2026.1/Vivado/settings64.sh >/dev/null 2>&1 || exit 98
(cd "$WT" && exec env H0_BOARD_UART_OUTPUT="$OUT" vivado -mode batch -log "$MON/vivado.log" -journal "$MON/vivado.jou" -source research/h0_board_uart_1a/implement.tcl) > "$MON/vivado.stdout" 2>&1 &
pid=$!
echo 'epoch,mem_available_kb,swap_free_kb,psi_full_avg10' > "$MON/memory.csv"
low=0; psi=0; verdict=
while kill -0 "$pid" 2>/dev/null; do
 av=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
 sf=$(awk '/SwapFree/{print $2}' /proc/meminfo)
 full=$(awk '/^full/{sub("avg10=","",$2);print $2}' /proc/pressure/memory)
 printf '%s,%s,%s,%s\n' "$(date +%s)" "$av" "$sf" "$full" >> "$MON/memory.csv"
 (( av < 204800 )) && low=$((low+1)) || low=0
 awk "BEGIN{exit !($full>40)}" && psi=$((psi+1)) || psi=0
 if (( low >= 6 || psi >= 12 )); then
  verdict="HOLD_MEMORY low=$low psi=$psi";pkill -TERM -P "$pid" || :;kill -TERM "$pid" 2>/dev/null || :
  sleep 5;pkill -KILL -P "$pid" || :;kill -KILL "$pid" 2>/dev/null || :;break
 fi
 sleep 5
done
wait "$pid"; rc=$?
{ date -u +%FT%TZ; grep -E 'MemAvailable|SwapFree' /proc/meminfo; echo "vivado_exit=$rc"; } > "$MON/memory_after.txt"
if [[ -n "$verdict" || "$rc" -eq 137 ]]; then echo "${verdict:-possible OOM exit 137}" > "$MON/HOLD_MEMORY";exit 97;fi
if (( rc == 0 )) && [[ ! -f "$OUT/IMPLEMENTATION_FINISHED" ]]; then echo 'missing completion marker' > "$MON/HOLD_INCOMPLETE";exit 96;fi
exit "$rc"
