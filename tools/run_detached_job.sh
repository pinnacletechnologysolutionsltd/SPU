#!/usr/bin/env bash
# Launch one deterministic long-running job under the user's systemd manager.
set -euo pipefail

usage() {
    echo "Usage: $0 --output DIR --timeout SECONDS [--unit NAME] [--notify-desktop] -- COMMAND [ARG ...]" >&2
    exit 2
}

out_dir=""
timeout_seconds=""
requested_unit=""
notify_desktop=1
while [ "$#" -gt 0 ]; do
    case "$1" in
        --output) [ "$#" -ge 2 ] || usage; out_dir="$2"; shift 2;;
        --timeout) [ "$#" -ge 2 ] || usage; timeout_seconds="$2"; shift 2;;
        --unit) [ "$#" -ge 2 ] || usage; requested_unit="$2"; shift 2;;
        --notify-desktop) notify_desktop=1; shift;;
        --) shift; break;;
        *) usage;;
    esac
done

[ -n "$out_dir" ] || usage
[ -n "$timeout_seconds" ] || usage
[ "$#" -gt 0 ] || usage
case "$timeout_seconds" in
    *[!0-9]*|0|"") echo "timeout must be a positive integer number of seconds" >&2; exit 2;;
esac
command -v systemd-run >/dev/null || {
    echo "systemd-run is unavailable; detached launch refused" >&2
    exit 1
}
systemctl --user show-environment >/dev/null || {
    echo "the user systemd manager is unavailable; detached launch refused" >&2
    exit 1
}

repo_root=$(git rev-parse --show-toplevel)
worker="$repo_root/tools/run_detached_job_worker.sh"
[ -x "$worker" ] || {
    echo "worker is not executable: $worker" >&2
    exit 1
}

case "$out_dir" in
    /*) out_abs="$out_dir";;
    *) out_abs="$repo_root/$out_dir";;
esac
out_abs=$(realpath -m -- "$out_abs")
case "$out_abs" in
    "$repo_root"/build/*) ;;
    *) echo "evidence directory must be a unique child of $repo_root/build" >&2; exit 2;;
esac
[ ! -e "$out_abs" ] || {
    echo "evidence directory already exists: $out_abs" >&2
    exit 1
}
mkdir -p "$out_abs"

base=$(basename "$out_abs" | tr -cs 'A-Za-z0-9_.-' '-' | sed 's/-$//')
if [ -n "$requested_unit" ]; then
    unit="$requested_unit"
else
    unit="spu-${base}-$(date -u +%Y%m%dT%H%M%SZ)-$$"
fi
case "$unit" in
    *[!A-Za-z0-9_.@-]*) echo "invalid systemd unit name: $unit" >&2; exit 2;;
esac

printf '%q ' "$@" > "$out_abs/command.txt"
printf '\n' >> "$out_abs/command.txt"
printf '%s\n' "$repo_root" > "$out_abs/working_directory.txt"
printf '%s\n' "$unit" > "$out_abs/unit_name"
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$out_abs/launch_time_utc"
git rev-parse HEAD > "$out_abs/git_commit"
git status --short > "$out_abs/git_status.txt"
{
    bash --version | head -n 1
    python3 --version 2>&1 || true
    yosys -V 2>&1 || true
    nextpnr-himbaechel --version 2>&1 || true
    nextpnr-xilinx --version 2>&1 || true
} > "$out_abs/tool_versions.txt"

if ! systemd-run --user --quiet --collect --setenv="PATH=$PATH" \
        --unit="$unit" --working-directory="$repo_root" \
        "$worker" "$out_abs" "$timeout_seconds" "$unit" \
        "$notify_desktop" -- "$@"; then
    printf '%s\n' "systemd-run failed before launch" > "$out_abs/launch_error"
    exit 1
fi
printf '%s\n' "$unit" > "$out_abs/LAUNCHED"
sync -f "$out_abs/LAUNCHED"

echo "LAUNCHED unit=$unit evidence=$out_abs"
echo "Return in a later agent session; inspect only COMPLETE, FAILED, or TIMEOUT."
