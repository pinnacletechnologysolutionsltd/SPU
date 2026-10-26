#!/usr/bin/env python3
"""Run a process group under a CLOCK_BOOTTIME budget, including suspend."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def clocks():
    return dict(boottime_ns=time.clock_gettime_ns(time.CLOCK_BOOTTIME),
                monotonic_ns=time.monotonic_ns(), utc_ns=time.time_ns())


def supervise(command, seconds, evidence, sample=clocks):
    started = sample()
    deadline = started['boottime_ns'] + int(seconds * 1_000_000_000)
    proc = subprocess.Popen(command, start_new_session=True)
    breach = False
    kill_at = None
    while True:
        now = sample()
        # Elapsed deadline wins even if a child finished while this host slept.
        if not breach and now['boottime_ns'] >= deadline:
            breach = True
            kill_at = now['boottime_ns'] + 10_000_000_000
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        code = proc.poll()
        if breach and (code is not None or now['boottime_ns'] >= kill_at):
            # Reap descendants too, including children which ignore TERM.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            code = proc.wait()
            break
        if code is not None:
            break
        time.sleep(0.02)
    ended = sample()
    breach = breach or ended['boottime_ns'] >= deadline
    result = dict(clock='CLOCK_BOOTTIME', timeout_seconds=seconds,
                  started=started, ended=ended,
                  elapsed_seconds=(ended['boottime_ns']-started['boottime_ns'])/1e9,
                  active_seconds=(ended['monotonic_ns']-started['monotonic_ns'])/1e9,
                  command_exit_code=code, elapsed_deadline_breached=breach,
                  exit_code=124 if breach else code if code >= 0 else 128-code)
    Path(evidence).write_text(json.dumps(result, indent=2)+'\n')
    return result['exit_code']


if __name__ == '__main__':
    if len(sys.argv) < 5:
        raise SystemExit('usage: run_elapsed_deadline.py SECONDS EVIDENCE -- COMMAND')
    seconds = int(sys.argv[1])
    if seconds <= 0 or sys.argv[3] != '--':
        raise SystemExit('usage: run_elapsed_deadline.py SECONDS EVIDENCE -- COMMAND')
    raise SystemExit(supervise(sys.argv[4:], seconds, sys.argv[2]))
