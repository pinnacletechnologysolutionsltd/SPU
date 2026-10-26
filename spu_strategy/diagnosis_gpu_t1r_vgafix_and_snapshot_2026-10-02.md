# VGAFIX display and repository snapshot diagnosis

**Date:** 2026-10-02  
**Status:** Snapshot cause established; display cause unresolved; redesigned verification contract prepared  
**Authorization:** Owner requested diagnosis before redesign; no new campaign or hardware operation launched during this work.

## 1. Reproduce the recorded snapshot failure

```bash
cat build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/snapshot_01/result.json
cat build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/snapshot_01/command_06.json
cat build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/snapshot_01/stderr.log
readlink build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout/.venv_plot/bin/python
readlink build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout/.venv_plot/bin/python3
cat .venv_plot/pyvenv.cfg
```

Exactly one terminal marker was `FAILED`, exit 1 after 9 seconds. Git identity,
status/diff recording, independent clone, detached checkout, and rsync all exited
0. The destination manifest then raised `external source symlink:
.venv_plot/bin/python`. The chain is `python` → `python3` → `/usr/bin/python3`,
currently resolving to `/usr/bin/python3.14`. It is a local virtual environment,
confirmed by `pyvenv.cfg`, rather than a project source dependency to relocate.

The helper excluded `.venv` and `venv` by exact root names. It did not exclude
`.venv_plot`. The full working-tree overlay deliberately includes ignored
source; rsync does not apply Git ignore rules automatically. Consequently the
source manifest included 3,029 `.venv_plot` entries out of 5,878, and rsync copied
the environment, including its interpreter symlinks. Git ignore status did not
prevent that copy. The manifest correctly rejected the external target.

The defect is the incomplete environment-exclusion policy. It is not a
regression failure, synthesis failure, timeout, or recurrence of the excluded
`build/` escape. `checkout/build` is a real directory; the rejection occurred
before chipdb copying and before any successor gate. The failed checkout and
all evidence are preserved. The one snapshot slot remains consumed.

Evidence: `diagnosis_01/diagnosis.json`,
`campaign_01/snapshot_interpretation_01.json`, and the original per-command logs
under `build/gpu/t1r_vgafix_control_verification_20261002/`.

## 2. Correct the policy before another snapshot

Use the [recovery contract](contract_gpu_t1r_vgafix_repository_recovery_2026-10-02.md).
Freeze explicit root environments `.venv`, `.venv_plot`, and `venv`. Derive
rsync root exclusions from the same set used by the manifest. Preserve ignored
source, including similarly named directories and nested `.venv_plot` source.
An unexpected root `pyvenv.cfg` directory halts before clone/rsync; it does not
silently broaden exclusions. Included symlinks must be relative and contained
before cloning, then pass destination containment checks after copying.

The revised helper preserves the previously reviewed build-directory guards.
Its frozen SHA-256 is
`c483c153c0f4bdacd1309e9308dd6e25722c0df6807a331c3597326d6d66486a`.
All 27 local fixtures passed, including a negative control reproducing the
failed helper's `.venv_plot` rejection, actual temporary rsync, preserved source
identity, early unknown-environment rejection, source-link checks, inherited
build-path rejection, and all four exact gate import/build guards. These are
local implementation checks; corrected-helper implementation review remains
pending. They do not constitute a production snapshot or full repository gate.

A read-only current inventory preview passed with root environments `.venv`
and `.venv_plot`, 2,850 included entries, and no included source symlinks at that
preview time. This is not a frozen campaign manifest; subsequent documentation
updates will be inputs to a later authorized preparation attempt. No corrected
production preparation, regression, synthesis, programming, STAT query, UART,
or signal capture was launched.

## 3. Diagnose the VGAFIX result separately

```bash
sha256sum build/spu_a7_100t_VGAFIX.bit
cat build/gpu/t1r_vgafix_control_20261002/control_01/program_01/result.json
cat build/gpu/t1r_vgafix_control_20261002/control_01/startup_stat_01.stdout
cat build/gpu/t1r_vgafix_control_20261002/control_01/hardware_result_01.json
```

The loaded file matches the exact historical color-bar artifact SHA-256
`a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379`.
Its existing header identifies VGAFIX frames, XC7A100T-FGG676-1, and generation
date 2026/09/04. The transfer reached 100%, programming exited 0, and startup
STAT was `0x401079fc` with all contract-required bits/error checks passing.
The result is supported by [hardware evidence §3.33](../docs/hardware_evidence.md#333--vgafix-display-control-programmingstartup-pass-visual-hold-2026-10-02).

The current top/pattern/timing/HAL/synthesis-source bytes match historical
anchor `bf00be07e74911755727f80adba7672dcab5668b`. The retained routed JSON has
VGA R/G/B on G8/G7/G5 and HSYNC/VSYNC on D5/E5. Those files support the archived
design context, but were not newly rebuilt or independently bound to the loaded
bit during this audit. Retained metrics report `b66b768`/184.74 MHz, whereas the
historical ledger reports `bf00be0`/170.97 MHz; do not silently substitute either
as a new timing result or rely on that contextual metadata for current identity.
The current load identity is the frozen bitstream hash.

The operator reports the same diagonal/crosshatch as T1r after startup and
visually confirms that the monitor harness goes to J10 on the same Wukong board
connected to DirtyJTAG. Preserve that confirmation in
`diagnosis_01/operator_path_confirmation.json`. It supports physical association
but is not an electrical continuity or waveform measurement. Post-load original
photo/video are still unavailable, so unchanged appearance is an operator report,
not measured pixel equality across configurations.

Thus the control is visual HOLD, and a GPU-specific arithmetic explanation is
not established. A successful configuration/startup does not establish a live
reset-released pixel pipeline or a correct signal at the monitor connector.
The remaining cause cannot be identified from these logs. The next discriminating
hardware experiment should measure current HSYNC, VSYNC, and RGB first at the
FPGA-side harness and then at the monitor-side plug, with declared probe mapping
and loading. The historical expected sync rates are 31.25 kHz and about 59.524 Hz
for this 25 MHz/800/525 design; current rates remain unmeasured. Correct source
signals but a corrupted display would direct investigation downstream; absent or
incorrect source signals would direct it toward clock/reset/output/configuration.

Draft and freeze instrument identity, channels, connection points, duration,
timeout, attempt counts, and evidence commands before that separate hardware
experiment. This diagnosis does not authorize a reload, reset, power-cycle,
rewiring, monitor adjustment, or capture under the exhausted control contract.
