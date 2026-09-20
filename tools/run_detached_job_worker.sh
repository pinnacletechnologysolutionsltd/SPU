#!/usr/bin/env bash
# Internal worker for run_detached_job.sh. May also be invoked directly by tests.
set -u

[ "$#" -ge 6 ] || exit 2
out_dir="$1"
timeout_seconds="$2"
unit="$3"
notify_desktop="$4"
shift 4
[ "$1" = "--" ] || exit 2
shift
[ "$#" -gt 0 ] || exit 2
case "$notify_desktop" in 0|1) ;; *) exit 2;; esac
case "$timeout_seconds" in *[!0-9]*|0|"") exit 2;; esac
[ -d "$out_dir" ] || exit 2
[ ! -e "$out_dir/COMPLETE" ] || exit 2
[ ! -e "$out_dir/FAILED" ] || exit 2
[ ! -e "$out_dir/TIMEOUT" ] || exit 2
[ ! -e "$out_dir/exit_status" ] || exit 2

started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
started_epoch=$(date +%s)
printf '%s\n' "$started" > "$out_dir/start_time_utc"
printf '%s\n' "$$" > "$out_dir/worker_pid"

set +e
timeout --signal=TERM --kill-after=10s "$timeout_seconds" \
    "$@" > "$out_dir/stdout.log" 2> "$out_dir/stderr.log"
rc=$?
set -e

ended=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ended_epoch=$(date +%s)
duration=$((ended_epoch - started_epoch))
if [ "$rc" -eq 0 ]; then
    outcome="COMPLETE"
elif [ "$rc" -eq 124 ]; then
    outcome="TIMEOUT"
else
    outcome="FAILED"
fi

printf '%s\n' "$rc" > "$out_dir/.exit_status.tmp.$$"
mv "$out_dir/.exit_status.tmp.$$" "$out_dir/exit_status"
printf '%s\n' \
    '{' \
    '  "format": "SPU_DETACHED_JOB_RESULT_V1",' \
    "  \"outcome\": \"$outcome\"," \
    "  \"exit_code\": $rc," \
    "  \"timeout_seconds\": $timeout_seconds," \
    "  \"duration_seconds\": $duration," \
    "  \"start_time_utc\": \"$started\"," \
    "  \"end_time_utc\": \"$ended\"," \
    "  \"systemd_unit\": \"$unit\"" \
    '}' > "$out_dir/.result.json.tmp.$$"
mv "$out_dir/.result.json.tmp.$$" "$out_dir/result.json"

sync -f "$out_dir/stdout.log"
sync -f "$out_dir/stderr.log"
sync -f "$out_dir/exit_status"
sync -f "$out_dir/result.json"
printf '%s\n' "$ended" > "$out_dir/.${outcome}.tmp.$$"
mv "$out_dir/.${outcome}.tmp.$$" "$out_dir/$outcome"
sync -f "$out_dir/$outcome"
if [ "$notify_desktop" -eq 1 ]; then
    notifier="${SPU_NOTIFY_SEND:-notify-send}"
    if command -v "$notifier" >/dev/null 2>&1; then
        if "$notifier" --app-name="SPU detached runner" \
                "SPU job $outcome" "$unit\n$out_dir" \
                > "$out_dir/notification.log" 2>&1; then
            printf '%s\n' "DELIVERED" > "$out_dir/notification_status"
        else
            printf '%s\n' "FAILED" > "$out_dir/notification_status"
        fi
    else
        printf '%s\n' "UNAVAILABLE" > "$out_dir/notification_status"
    fi
fi
exit "$rc"
