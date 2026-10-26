# Engineering Contract: T1r Q1 Artix-7 Route Gate

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-Q1-ROUTE-GATE-2026-10-01`  
**Status:** DRAFT — route execution NOT AUTHORIZED  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `hardware/boards/artix7/build_a7.sh` and owner evidence review

## 0. Purpose and scope

Run the T1r Artix-7 100T GPUVGA synthesis/place-and-route/pack build after the focused Q1 recovery, repository gate, and mandatory Padé baseline build have passed. This contract covers the T1r route only. It does not authorize FPGA programming, UART traffic, display observation, or any other hardware action.

The prior gates are recorded in [focused recovery v2](../build/gpu/t1r_palette_pair_20261001/recovery_v2/focused_campaign_summary.md), [repository gate evidence](../build/gpu/t1r_palette_pair_20261001/repo_gate/run_01/result.json), and [Padé baseline closeout](../build/gpu/t1r_palette_pair_20261001/pade_synthesis/run_01/qualification_summary.txt). Passing this route gate would qualify the T1r artifact for a separately authorized SRAM load and scaled-visibility tranche only after route evidence is reviewed.

## 1. Frozen source and profile identity

Repository commit: `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`.

The route input manifest is `build/gpu/t1r_palette_pair_20261001/route_preflight/source_hashes.txt`. It contains 103 inputs: the frozen Padé synthesis inputs, the GPUVGA-specific synthesis source list and top, GPUVGA XDC, metrics collector, chip database, and detached runner. Its SHA-256 is `524d64e0acac462fc6b030c336a3bf8709f203ce7ebca79be29521e8898a59d1`.

The route uses the T1r Q1 profile defined in the [Q1 implementation contract](contract_gpu_t1r_palette_pair_q1_2026-10-01.md): Artix-7 100T, `GPUVGA`, seed 1, 25 MHz, and artifact tag `T1R_PALETTE_PAIR_MATERIAL_Q1`. The exact enabled feature tuple is:

```text
GPU_T1D_UART=1
FOUR_PRIMITIVE_SCENE=1
T1I_UV_SCENE=1
T1L_PIPELINE_PARTITION=1
GPU_POST_WINNER_REG=1
T1R_PALETTE_PAIR_MATERIAL=1
A7_ARTIFACT_TAG=T1R_PALETTE_PAIR_MATERIAL_Q1
```

The exact disabled material feature tuple is:

```text
T1O_PER_PRIMITIVE_MATERIAL=0
T1P_PER_PRIMITIVE_PREDICATES=0
T1Q_TRUTH_TABLE_MATERIAL=0
```

Other optional GPU profiles and diagnostics must remain at their `build_a7.sh` defaults and must print disabled in the build profile. The tool log must identify device `xc7a100tfgg676-1`, spin `GPUVGA`, `A7_FREQ=25`, seed `1`, and the exact T1r bitstream name below.

Before launch, run and record these preflight checks in `build/gpu/t1r_palette_pair_20261001/route_preflight/preflight.txt`; halt on any mismatch:

```bash
git rev-parse HEAD
sha256sum build/gpu/t1r_palette_pair_20261001/route_preflight/source_hashes.txt
sha256sum -c build/gpu/t1r_palette_pair_20261001/route_preflight/source_hashes.txt
git status --short
```

Required values:

```text
HEAD: 4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f
source_hashes.txt: 524d64e0acac462fc6b030c336a3bf8709f203ce7ebca79be29521e8898a59d1
```

The working tree is dirty. Preserve its launch-time `git status --short` in the preflight record; the 103-input hash manifest is the source identity gate. Do not edit, stage, or clean route inputs. The following fixed build outputs were absent when this contract was drafted; verify they remain absent before launch so the authorized route cannot silently overwrite earlier evidence:

```text
build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json
build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.pnr.json
build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.pnr.fasm
build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.pnr.frames
build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.nextpnr.log
build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.timing_report.json
build/metrics/artix7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json
build/metrics/artix7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.md
```

If any frozen input differs or any fixed output path exists, halt before launch and revise the contract after recording the conflicting evidence.

## 2. One bounded route attempt

Authorize one detached attempt with a 1,800-second timeout and 1,800-second cumulative budget. The evidence directory must be new:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_palette_pair_20261001/build_seed1/run_01 \
  --timeout 1800 --notify-desktop -- \
  env A7_SEED=1 A7_FREQ=25 GPU_T1D_UART=1 \
    FOUR_PRIMITIVE_SCENE=1 T1I_UV_SCENE=1 \
    T1L_PIPELINE_PARTITION=1 GPU_POST_WINNER_REG=1 \
    T1O_PER_PRIMITIVE_MATERIAL=0 T1P_PER_PRIMITIVE_PREDICATES=0 \
    T1Q_TRUTH_TABLE_MATERIAL=0 T1R_PALETTE_PAIR_MATERIAL=1 \
    A7_ARTIFACT_TAG=T1R_PALETTE_PAIR_MATERIAL_Q1 \
    bash hardware/boards/artix7/build_a7.sh 100t gpuvga all
```

When the launcher reports `LAUNCHED`, record its systemd unit and evidence path, then end the turn. Do not poll or wait for completion in that turn. Interpret the run in a later invocation only when exactly one durable terminal marker exists: `COMPLETE`, `FAILED`, or `TIMEOUT`.

## 3. Acceptance and evidence closeout

Pass requires all of the following:

1. Exactly one durable `COMPLETE` marker, no `FAILED` or `TIMEOUT` marker, and `result.json` with exit code 0.
2. The build log shows the exact Artix-7 100T T1r Q1 profile from §1, including seed 1 and 25 MHz.
3. The final post-route nextpnr timing result for `clk_pixel` is at least `25.00 MHz` and reports `PASS at 25.00 MHz`. Use the final routed occurrence in the log; an earlier pre-route estimate does not satisfy this condition.
4. The following outputs exist and are nonempty:

   ```text
   build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
   build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json
   build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.pnr.json
   build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.pnr.fasm
   build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.pnr.frames
   build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json.nextpnr.log
   build/metrics/artix7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.json
   build/metrics/artix7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.md
   ```

After the terminal marker is available, copy these outputs into `build/gpu/t1r_palette_pair_20261001/build_seed1/run_01/artifacts/`, record their SHA-256 hashes there, and preserve the final routed `clk_pixel` timing line in `timing_evidence.txt`. Also preserve the optional native `.timing_report.json` if the installed nextpnr supports it; the nextpnr log and metrics JSON remain mandatory timing evidence.

Any failed command, timeout, unavailable or multiple terminal markers, nonzero exit, profile mismatch, missing/empty output, or `clk_pixel` timing below 25.00 MHz is not a pass. The launched attempt consumes the single slot on every outcome. No retry, timeout extension, seed change, source change, or substitute build is authorized under this contract.

## 4. Stop and handoff boundary

After interpreting the durable evidence, report the T1r route result and stop. Even a route pass does not authorize FPGA programming, SRAM loading, UART transport, visual observation, or silicon claims. Those require a separate owner-authorized hardware contract.

| Evidence claim | Current state |
|---|---|
| T1r Q1 focused functional gate | PASS — recovery v2 |
| Repository hygiene/regression gate | PASS — one durable `COMPLETE`, exit 0 |
| Mandatory Padé baseline build | PASS — one durable `COMPLETE`, `clk_fast` 39.86 MHz at 25 MHz target |
| T1r Artix-7 100T route | NOT RUN — not authorized yet |
| T1r hardware/interface/silicon | NOT RUN — separate authorization required |
