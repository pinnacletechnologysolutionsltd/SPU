# Detached Job Runner

Use `tools/run_detached_job.sh` for deterministic synthesis, place-and-route,
full regression, and campaign commands expected to exceed 60 seconds. The
runner delegates process lifetime to the per-user systemd manager and writes a
durable evidence protocol under `build/`.

## Launch

Choose a unique evidence directory and freeze the wall-clock timeout before
launch:

```bash
tools/run_detached_job.sh \
  --output build/regressions/verify_repo_20260910_01 \
  --timeout 3600 \
  --notify-desktop \
  -- bash tools/verify_repo.sh
```

For the mandatory Artix gate:

```bash
tools/run_detached_job.sh \
  --output build/artix7/rplu2pade_gate_20260910_01 \
  --timeout 7200 \
  -- env A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

The launcher prints the systemd unit and absolute evidence path after systemd
accepts the job. At that point, stop the agent turn. Do not poll.

Desktop notification is enabled by default; `--notify-desktop` is accepted as
an explicit, idempotent spelling. After writing the terminal marker, the worker
uses `notify-send` to report the unit, outcome, and evidence directory. It
records `DELIVERED`, `FAILED`, or `UNAVAILABLE` in `notification_status`.
Notification failure is non-fatal and never changes the command outcome.

## Completion protocol

Every launched directory contains provenance files such as:

```text
command.txt
git_commit
git_status.txt
launch_time_utc
LAUNCHED
tool_versions.txt
unit_name
working_directory.txt
```

The worker adds `stdout.log`, `stderr.log`, `start_time_utc`, `worker_pid`,
`exit_status`, and `result.json`. It then atomically publishes exactly one
terminal marker after flushing the result files:

* `COMPLETE`: command exited 0.
* `FAILED`: command exited nonzero.
* `TIMEOUT`: GNU `timeout` returned 124 at the predeclared wall-clock bound.

No terminal marker means no result is available. A missing unit or partial log
does not change that rule.

## Later-session inspection

Read the marker and small result first:

```bash
ls build/regressions/verify_repo_20260910_01/{COMPLETE,FAILED,TIMEOUT} 2>/dev/null
sed -n '1,120p' build/regressions/verify_repo_20260910_01/result.json
```

Inspect logs and reports only after a terminal marker exists. Preserve the
directory unchanged as evidence; use a new unique directory for any authorized
rerun.

## Host prerequisite

The launcher requires a functioning `systemd --user` manager. Desktop sessions
normally provide one. To allow jobs to survive a full user logout, an
administrator must enable lingering once:

```bash
loginctl enable-linger "$USER"
```

The runner does not enable lingering, restart services, or modify host policy.
It refuses detached launch when the user manager is unavailable. Jobs are not
promised to survive reboot.
