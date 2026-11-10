# CPU-REPRO desktop run: second Gen-1 configuration-payload reproduction (2026-11-06)

**Disposition: PASS-BIT-EXACT for the configuration payload (single run), with 0 report differences against the golden build.**
A fresh Vivado 2026.1 implementation on a second host, made with the unchanged portable flow, produced the golden Gen-1 configuration payload.
It is **not** a hardware observation: nothing was programmed, and it adds no entry to [`docs/hardware_evidence.md`](hardware_evidence.md).
The frozen package and the [CPU-REPRO-1B record](../hardware/boards/artix7/wukong_v3/cpu_v02/portable/REPRO_1B_RESULT.md) are unchanged.

| Item | Value |
|---|---|
| Host | Ubuntu desktop (Linux 7.0.0-42), MemTotal 15,804,680 kB, MemAvailable 11,805,308 kB at launch; no memory waiver |
| Repository | `e7d37aa` (`dev/next`); `git status --porcelain -- hardware tools` empty at launch (preflight `dirty=0`) |
| Tool / part | Vivado 2026.1 SW Build 6511674, `xc7a100tfgg676-1` |
| Run | `repro1-desktop-02`, detached unit `spu-repro1-desktop-02-job-20261106T071035Z-47841`, `COMPLETE`, exit 0, 1160 s (limit 5400 s) |
| Package verification | 45 of 45 `PACKAGE_SHA256.txt` / `PORTABLE_SHA256.txt` entries OK (`meta/package_verify.txt`) |
| Generated `.bin` | `cc259988b32dcd890a25c8a1765c6a28e3fafa280bcaed1aa5073f552dbc156c` = golden payload (same value as CPU-REPRO-1B) |
| Generated `.bit` | `bf0e8f7be4b8c902674e119da52a3dda8c327b4b468a92f6941154722590f07a`; differs from golden `442a229e…` in the header build date/time, as expected |
| `synth.dcp` / `routed.dcp` | `bdd6b839f0a2ee230de542d344af4413db9da993529a4e84098e3cd80e3147e5` / `ff0092bab316ace0f6d726018789c9b05b821f1af0975c91ae5ff173ebaa6542` (checkpoint bytes are not expected to match) |
| Implementation | 28,107 nets fully routed; WNS +6.360 ns, WHS +0.060 ns, 0 failing setup or hold endpoints (same values as golden and CPU-REPRO-1B); 0 `ERROR` and 0 `CRITICAL WARNING` lines in the three phase logs other than echoed script source |
| Peak RSS | synth 2.52 GB, route 2.56 GB, bitstream 3.18 GB |
| Evidence (untracked, `build/cpu-repro-1/`) | `repro1-desktop-02/` 83 files, tree manifest `d30a1c3b3e0ed5d050929992136d366895ac4429f0b7547dff38db6c8efc18b9`; `repro1-desktop-02-job/` 18 files, `e7b76a4235af2d2930ce3a06f78c6ed2c078b75bf38384d093fff692dac67d0b` (sha256 of the sorted `sha256sum` listing) |

Launch command (repository root):

    tools/run_detached_job.sh --output build/cpu-repro-1/repro1-desktop-02-job --timeout 5400 -- \
      env VIVADO_SETTINGS=/home/john/2026.1/Vivado/settings64.sh \
      bash hardware/boards/artix7/wukong_v3/cpu_v02/portable/run_repro.sh repro1-desktop-02

The detached runner forwards only `PATH` into the systemd unit, so `VIVADO_SETTINGS` is set inside the command with `env`.
No frozen script was edited.

## Earlier attempt
`repro1-desktop-01` (job evidence `build/cpu-repro-1/repro1-desktop-01-job/`, 18 files, tree manifest `04388c620962961432678c068eeb17e396d427817ddb24b15f3af318a05bf412`) exited 94 at preflight (`PREFLIGHT_HOLD 94: VIVADO_SETTINGS not set or missing`) within one second, because the variable was set outside the unit.
Vivado did not start and no build directory was created.

## Report-level comparison (run separately after the golden directory was recovered)
Inside the run, `compare.py` did not complete (`KeyError: 'GOLDEN_VIVADO'`; `meta/compare_rc.txt` = 1): the golden Vivado directory was in a laptop migration archive whose first copy failed integrity checks.
A second copy of that archive (`spu-gate.tar.zst`, sha256 `6245a309f68f01c82f0488aacf1d5fa276c8bd9c547f29ae81620272c3a0ba68`, matching the laptop's `SHA256SUMS`) was restored to `/home/john/.local/gate` on 2026-11-06; the golden `routed.dcp` is `48e0e161…` as recorded.
The unchanged comparator was then run against the finished run, writing its output outside the run directory:

    GOLDEN_VIVADO=/home/john/.local/gate/spu-int3b-c3efc18/build/vivado \
      python3 -I hardware/boards/artix7/wukong_v3/cpu_v02/portable/compare.py \
      build/cpu-repro-1/repro1-desktop-02 build/cpu-repro-1/repro1-desktop-02-compare/COMPARE_RESULT.txt

Result: rc 0, `golden identity OK`, 48 reports and records `SAME`, `report differences: 0`, `.bin` EQUAL to golden, `.bit` different only in the header date/time, checkpoint hashes informational; `VERDICT PASS-BIT-EXACT`.
Evidence: `build/cpu-repro-1/repro1-desktop-02-compare/` (untracked; 3 files, `COMPARE_RESULT.txt` sha256 `876a154356332842aea7b5e4f6b76b600eacec05a48d7b056cd55332c7f3672a`; `MANIFEST.sha256` checks from `build/cpu-repro-1/`). The run directory itself was not modified.

## Limitations
- One run on this host. Vivado 2026.1 build 6511674 only; determinism across other installs or versions is not established.
- Physical behaviour is covered only by the separate observations in [`docs/hardware_evidence.md`](hardware_evidence.md) §3.40–3.43 and §3.47–3.51.
