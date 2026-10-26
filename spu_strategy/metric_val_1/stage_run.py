#!/usr/bin/env python3
"""Run one stage: RLIMIT_AS, hard wall deadline, process-group kill, rusage. Writes <stages>/<name>.json."""
import argparse, json, os, resource, signal, subprocess, sys, time

p = argparse.ArgumentParser()
p.add_argument("--name", required=True); p.add_argument("--stages", required=True)
p.add_argument("--cwd", required=True); p.add_argument("--timeout", type=float, required=True)
p.add_argument("--deadline-epoch", type=float, required=True)
p.add_argument("--as-bytes", type=int, default=2 * 1024**3)
p.add_argument("--home", required=True)
p.add_argument("cmd", nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
t0 = time.time()
budget = min(a.timeout, a.deadline_epoch - t0)
rec = {"name": a.name, "cmd": cmd, "as_bytes": a.as_bytes, "timeout_s": round(budget, 3)}
if budget <= 0:
    rec.update(status="SKIPPED_BUDGET", rc=None, wall_s=0.0, maxrss_kib=0)
else:
    env = {"PATH": os.environ.get("PATH", ""), "HOME": a.home, "TMPDIR": a.home,
           "PYTHONDONTWRITEBYTECODE": "1", "LC_ALL": "C"}
    lim = lambda: resource.setrlimit(resource.RLIMIT_AS, (a.as_bytes, a.as_bytes))
    log = open(os.path.join(a.stages, a.name + ".log"), "wb")
    pr = subprocess.Popen(cmd, cwd=a.cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                          preexec_fn=lambda: (os.setsid(), lim()))
    status = None
    try:

        pr.wait(timeout=budget)
        status = "OK" if pr.returncode == 0 else "NONZERO"
    except subprocess.TimeoutExpired:
        os.killpg(pr.pid, signal.SIGKILL); pr.wait(); status = "TIMEOUT"
    try: os.killpg(pr.pid, signal.SIGKILL)   # reap stragglers
    except ProcessLookupError: pass
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    rec.update(status=status, rc=pr.returncode, wall_s=round(time.time() - t0, 3),
               maxrss_kib=ru.ru_maxrss)
json.dump(rec, open(os.path.join(a.stages, a.name + ".json"), "w"), indent=1)
print(rec["name"], rec["status"], rec.get("rc"), rec["wall_s"])
