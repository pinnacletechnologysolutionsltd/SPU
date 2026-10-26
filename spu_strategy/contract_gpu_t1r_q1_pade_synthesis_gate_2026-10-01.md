# Engineering Contract: T1r Q1 Mandatory Padé Baseline Build

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-Q1-PADE-SYNTHESIS-GATE-2026-10-01`  
**Status:** DRAFT — execution NOT AUTHORIZED  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `hardware/boards/artix7/build_a7.sh` and owner evidence review

## 0. Purpose and scope

Run the mandatory Artix-7 100T Padé baseline build as a separate qualification layer after the T1r focused gate and repository gate pass. This contract authorizes no T1r-specific synthesis/place-and-route, FPGA programming, UART traffic, visual observation, or other hardware activity.

The exact command uses the build script's `all` target. It runs Padé synthesis, place-and-route, and bitstream packing; it is not a synthesis-only command. Its outputs qualify the Padé baseline build only. A pass does not qualify the T1r design or authorize hardware work.

## 1. Frozen source and preflight

The frozen repository commit is `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`. The Padé source manifest is `build/gpu/t1r_palette_pair_20261001/pade_preflight/source_hashes.txt`, with SHA-256 `7fc8db22d56600a00df6ae048470050b67d1a5ca5fac86506b22348c167d0b37`; it contains 74 source/configuration inputs.

Before launch, run these commands and stop on any mismatch:

```bash
git rev-parse HEAD
sha256sum build/gpu/t1r_palette_pair_20261001/pade_preflight/source_hashes.txt
sha256sum -c build/gpu/t1r_palette_pair_20261001/pade_preflight/source_hashes.txt
git status --short
```

Required values:

```text
HEAD: 4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f
source_hashes.txt: 7fc8db22d56600a00df6ae048470050b67d1a5ca5fac86506b22348c167d0b37
```

Save the complete preflight output and launch-time working-tree status in `build/gpu/t1r_palette_pair_20261001/pade_preflight/preflight.txt`. Do not edit, stage, or clean repository source. The launcher will also record its own repository identity and dirty status.

The build overwrites these existing fixed-path outputs. Preserve them before launch under `build/gpu/t1r_palette_pair_20261001/pade_preflight/prior_artifacts/`, then verify the backup hashes:

```text
b2852718dc607bd0f866a4539adcf6f82ad37577e2c869c73614e81172014785  build/spu_a7_100t_RPLU2PADE.bit
108c3963b9d3f3d770b1536f372c96e56a031a15806cfdc4759a356bdb6962c3  build/spu_a7_100t_RPLU2PADE.json
1571d945a2777a464713d28059c1239ace56c4f6ea62f4bfba9b906ed1a0e6c5  build/spu_a7_100t_RPLU2PADE.json.nextpnr.log
ef5cafd8ef92bf1bac149cc45aa55fd349a72cb2fc8c984ec61de4738dfd2590  build/spu_a7_100t_RPLU2PADE.json.pnr.fasm
81531b558b89aef50e6fcb25e0599f8a1c08843f7b4b69fa2be41c982a16e70d  build/spu_a7_100t_RPLU2PADE.json.pnr.frames
fa8644569637691a1e6e98e04469a835b65ad5114805aa7ece7f1ee43d4248cb  build/spu_a7_100t_RPLU2PADE.json.pnr.json
```

Use the exact frozen filenames with a clear backup prefix/suffix, preserve metadata where available, and store the copy command output and hash verification in `preflight.txt`. Halt before launch if any source hash differs, a required prior artifact is missing, or a backup hash does not match.

## 2. One bounded baseline build

Authorize one attempt with a 1,800-second per-attempt timeout and 1,800-second cumulative budget. Use a new evidence directory:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_palette_pair_20261001/pade_synthesis/run_01 \
  --timeout 1800 --notify-desktop -- \
  env A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

The profile must resolve to Artix-7 100T / `rplu2pade`, 25 MHz, seed 1, and the script's frozen defaults: `FP4_STRUCTURED=1`, `FP4_BACKEND_SEQUENTIAL=0`, `A7_SYNTH_ABC9=0`, `PADE_DEBUG_TRACE=0`, `PADE_PIPELINED=0`, and `PIPELINED_RNS_CHECK=0`. Capture the build's printed configuration in the durable job log. Stop if it differs.

When the launcher reports `LAUNCHED`, record the systemd unit and evidence path, then end the turn. Do not poll or wait for completion in that turn. A later invocation may interpret the result only when exactly one durable terminal marker exists: `COMPLETE`, `FAILED`, or `TIMEOUT`.

Pass requires exactly one `COMPLETE` marker, `result.json` exit code 0, the expected profile in the build log, and nonempty outputs at all six fixed paths listed in §1. Preserve the result and output hashes in the run evidence directory. A failed build, timeout, missing/multiple terminal markers, missing result, profile mismatch, or missing output is not a pass. The attempt is consumed on any outcome; no retry, timeout extension, or alternate command is allowed under this contract.

## 3. Stop and handoff boundary

After interpreting the durable result, report the Padé baseline build outcome and stop. A pass is only the mandatory Padé baseline build evidence. It does not authorize T1r synthesis/place-and-route or hardware activity; each requires a separate owner decision and contract.

| Evidence claim | Starting state |
|---|---|
| T1r Q1 focused functional gate | PASS — recovery v2 |
| Repository hygiene/regression gate | PASS — one durable `COMPLETE`, exit 0 |
| Padé baseline synthesis/place-and-route/pack | NOT RUN — not authorized yet |
| T1r synthesis/place-and-route | NOT RUN — separate authorization required |
| Hardware/interface/silicon | NOT RUN — separate authorization required |
