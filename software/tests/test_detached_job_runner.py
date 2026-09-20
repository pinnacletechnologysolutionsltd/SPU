#!/usr/bin/env python3
"""Deterministic tests for the detached-job worker's durable protocol."""
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "tools/run_detached_job_worker.sh"


def run_case(command, expected_rc, expected_marker, notify="0", env=None):
    with tempfile.TemporaryDirectory(prefix="spu-detached-test-") as tmp:
        out = Path(tmp)
        completed = subprocess.run(
            [str(WORKER), str(out), "1", "test-unit", notify, "--", *command],
            cwd=ROOT, check=False, env=env,
        )
        assert completed.returncode == expected_rc
        assert (out / expected_marker).is_file()
        markers = [name for name in ("COMPLETE", "FAILED", "TIMEOUT")
                   if (out / name).exists()]
        assert markers == [expected_marker]
        assert int((out / "exit_status").read_text()) == expected_rc
        result = json.loads((out / "result.json").read_text())
        assert result["outcome"] == expected_marker
        assert result["exit_code"] == expected_rc
        if notify == "1":
            assert (out / "notification_status").read_text().strip() == "FAILED"
        assert result["systemd_unit"] == "test-unit"
        return (out / "stdout.log").read_text(), (out / "stderr.log").read_text()


def main():
    stdout, stderr = run_case(
        ["bash", "-c", "printf out; printf err >&2"], 0, "COMPLETE")
    assert stdout == "out"
    assert stderr == "err"
    run_case(["bash", "-c", "exit 7"], 7, "FAILED")
    run_case(["bash", "-c", "sleep 2"], 124, "TIMEOUT")
    env = dict(os.environ, SPU_NOTIFY_SEND="/bin/false")
    run_case(["bash", "-c", "exit 0"], 0, "COMPLETE", notify="1", env=env)
    print("PASS: detached job worker success/failure/timeout protocol")


if __name__ == "__main__":
    main()
