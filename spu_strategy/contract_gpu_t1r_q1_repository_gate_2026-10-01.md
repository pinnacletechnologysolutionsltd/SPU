# Engineering Contract: T1r Q1 Repository Gate

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-Q1-REPOSITORY-GATE-2026-10-01`  
**Status:** DRAFT — repository gate execution NOT AUTHORIZED  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `tools/verify_repo.sh` and owner evidence review

## 0. Purpose and scope

Run only the repository hygiene/regression gate after the T1r Q1 focused recovery v2 PASS. This contract does not authorize Padé synthesis, T1r synthesis/place-and-route, FPGA programming, UART traffic, visual observation, or other test/build commands.

The focused gate closeout is [recovery v2](../build/gpu/t1r_palette_pair_20261001/recovery_v2/focused_campaign_summary.md). It records four successful fresh invocations, the 35-input source manifest, and a cumulative time of approximately 148.6 seconds. The repository gate is the next isolated qualification layer; its result does not authorize the next layer.

## 1. Frozen source and preflight

The repository baseline is commit `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`.

Before launching, run these preflight commands and stop on any mismatch:

```bash
git rev-parse HEAD
sha256sum build/gpu/t1r_palette_pair_20261001/recovery_v2/source_hashes.txt
tail -n +2 build/gpu/t1r_palette_pair_20261001/recovery_v2/source_hashes.txt | sha256sum -c -
sha256sum run_all_tests.py
git status --short
```

Required values:

```text
HEAD: 4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f
source_hashes.txt: 5d27bdb368a5d22db8180314772f2b60f88324777f2aa7bae8f8dd1eaef03d13
run_all_tests.py: d1f5a3c4cf11013af16ca64fffc6d79c9fe8b44f43af7a1d07dafa65608586e5
```

Save the preflight output and current `git status --short` to `build/gpu/t1r_palette_pair_20261001/recovery_v2/repo_gate_preflight.txt` before launch. The working tree is already dirty; preserve and review its launch-time status snapshot. Do not edit, stage, or clean repository files under this contract. Halt if the commit or any frozen hash differs from the listed values.

## 2. Single bounded gate

Authorize one attempt only, with a 1,800-second per-attempt timeout and 1,800-second cumulative campaign budget. The evidence directory is unused and must be a new child of `build/`.

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_palette_pair_20261001/repo_gate/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

When the launcher reports `LAUNCHED`, record its systemd unit and evidence path, then end the turn. Do not poll or wait for completion in that turn. A later invocation may interpret the run only when exactly one durable terminal marker exists: `COMPLETE`, `FAILED`, or `TIMEOUT`.

Pass requires exactly one `COMPLETE` marker, `result.json` with exit code 0, and the repository gate's own successful completion record. `FAILED`, `TIMEOUT`, absent or multiple markers, missing result data, or a failed repository subcheck is not a pass. A launched attempt consumes the sole slot regardless of outcome. Do not retry, extend the timeout, substitute a command, or proceed to another qualification layer under this contract.

## 3. Stop and handoff boundary

After interpreting the durable terminal evidence, report the repository gate result and stop. Even a pass does not authorize Padé synthesis. That gate requires a separate owner decision and its own one-attempt contract.

| Evidence claim | Starting state |
|---|---|
| T1r Q1 focused functional gate | PASS — recovery v2 |
| Repository hygiene/regression gate | NOT RUN |
| Mandatory Padé synthesis | NOT RUN; not authorized here |
| T1r synthesis/place-and-route | NOT RUN; not authorized here |
| Hardware/interface/silicon | NOT RUN; not authorized here |
