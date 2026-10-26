"""Local packaging smoke test; not a new cross-implementation qualification."""
import datetime
import json
import pathlib
import subprocess
import sys
import tempfile
import time

source = pathlib.Path(sys.argv[1]).resolve()
here = pathlib.Path(__file__).resolve().parent
output = pathlib.Path(sys.argv[2]).resolve()
output.mkdir()  # Refuse evidence overwrite.
start = time.monotonic()
with tempfile.TemporaryDirectory(prefix="sim-public0-") as scratch:
    clone = pathlib.Path(scratch) / "spu-sim"
    commands = [
        ["git", "clone", "--no-local", "--no-checkout", str(source), str(clone)],
        ["git", "-C", str(clone), "checkout", "--detach",
         "c1e0676eee5d2398b8d90eec43bd55b2d2f6b924"],
        ["bwrap", "--ro-bind", "/", "/", "--tmpfs", "/home",
         "--tmpfs", "/opt", "--tmpfs", "/tmp", "--tmpfs", "/run",
         "--bind", scratch, "/tmp/work", "--ro-bind", str(here / "quickstart.sh"),
         "/tmp/workflow.sh", "--dev", "/dev", "--proc", "/proc", "--unshare-all",
         "--clearenv", "--setenv", "PATH", "/usr/bin:/bin",
         "--setenv", "HOME", "/tmp", "--setenv", "LC_ALL", "C",
         "--chdir", "/tmp/work/spu-sim", "--", "/bin/sh", "-eux", "/tmp/workflow.sh"],
    ]
    records = []
    for index, command in enumerate(commands):
        result = subprocess.run(command, capture_output=True, text=True, timeout=55)
        (output / f"step_{index}.log").write_text(result.stdout + result.stderr)
        records.append({"command": command, "exit": result.returncode})
        if result.returncode:
            break
    report = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "elapsed_seconds": round(time.monotonic() - start, 3),
              "steps": records, "pass": len(records) == 3 and
              all(r["exit"] == 0 for r in records),
              "limit": "55 seconds per subprocess; caller bounds total runtime and memory",
              "scope": "local independent clone; shared host OS/toolchain; no public fetch"}
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["pass"] else 1)
