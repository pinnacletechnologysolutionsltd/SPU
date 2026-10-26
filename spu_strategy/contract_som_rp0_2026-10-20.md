# Engineering Contract: SOM-RP0 — RP2350 Sensor Classification Feasibility

**Date:** 2026-10-20
**Contract ID:** `contract_som_rp0_2026-10-20.md`
**Status:** DRAFT. RP0a awaits owner approval. RP0b is not authorized by this document.

**Roles:** Spec Author: Claude (Opus 5.5), with coordinator review.
Halt-and-Flag Implementer: Claude.
Integration Auditor: the focused test commands below.

**Context.** The SOM was shelved on 2026-09-03, and its research closure on 2026-09-11
ended "application advantage not demonstrated". This contract **deliberately reopens
the SOM for feasibility only**: exact semantics and timing on the RP2350. It does not
reopen the advantage question. The FPGA SOM RTL and its silicon evidence stay
untouched as the future acceleration option.

---

## Tranche RP0a — host-only, Class A

### 1. Objective and scoped files

Produce a fixed-width, portable C BMU that reproduces the existing rational SOM
semantics exactly. It must compile unchanged for both the host and the RP2350
(Cortex-M33), and its overflow behaviour must be declared rather than wrapping.

- **New files, under `research/som_rp0/` only:**
  - `bmu.h` and `bmu.c`: the BMU, in C99 with no allocation and no floating point;
  - a host harness;
  - `oracle_compare.py`;
  - `FINDINGS.md`.
- **Read-only references:**
  - `software/lib/rational_som.py` is the oracle, with unbounded integers;
  - `software/common/include/spu_rational_som.h` and `spu_quadray.h` are references only and are **not** reused (see the halt condition in §3.1);
  - `hardware/rtl/core/spu13/spu_som_bmu.v` and the SOM-v1 gatekeeper path define the width and overflow semantics;
  - `docs/SOM_V1_PRODUCT_CONTRACT.md` defines the map format.
- **Out of scope:**
  - no firmware under `hardware/rp2350/` or `hardware/rp_common/`;
  - no RTL, simulator or product-contract edits;
  - no training, and no bench work.

### 2. Invariants (the "Never" list)

- [ ] Exact arithmetic only. No float anywhere, including the harness's expected values.
- [ ] No silent overflow. Every intermediate either fits by proof, or the result is a declared refusal (`OVERFLOW`) with no partial output.
- [ ] The semantics match the oracle bit for bit: winner, runner-up, label, exact best and second distances, confidence gap and ambiguity flag. Ties go to the lowest node id.
- [ ] The map format equals SOM v1: 4 features, signed 18-bit Q(√3) pairs, checksummed feature weights. Any extension is a separate, explicitly named profile.
- [ ] No vacuous assertions (AGENTS.md §3.5).
- [ ] Results are labelled `simulation-only` / `host-only`. No silicon claim is made.

### 3. Implementation steps

1. **Halt-and-flag width review, before any code.** Read `spu_som_bmu.v`: its accumulators are declared 32-bit (`q_accum_p` / `q_accum_q`), while its outputs are 64-bit. Read the gatekeeper overflow boundary too. Record the exact representable range and the overflow outcome the RTL implements. Note: the C++ `rs_lt` takes int32 differences of accumulated distances, which is not width-safe for 18-bit features. **If the RTL and the oracle disagree about overflow, HALT and report** before choosing the C semantics.
2. **Freeze the width contract in `bmu.h`:**
   - feature, prototype and weight coefficient ranges;
   - the worst-case bit width of each intermediate (difference, surd square, weighted term, 4-term sum);
   - the surd ordering test. It needs (Δp)² against 3(Δq)², so state whether 64-bit suffices under the frozen ranges or a 128-bit comparison is required. The M33 has a 32×32→64 multiply-accumulate but no native 128-bit type.
3. **Implement the BMU.** Use a stable lowest-id tie-break, track the runner-up, compute the gap, and apply the ambiguity threshold. The function returns status `OK`, `OVERFLOW`, `INVALID_MAP` or `NO_NODES`.
4. **Write `oracle_compare.py`.** It drives the host build over these fixtures and compares every output field:
   - the 7-node `tiny_hex_fixture`;
   - the checked Iris v1 map;
   - generated cases: exact ties, zero gap, surd-valued features, and values near the sign boundary p² ≈ 3q²;
   - maximum-magnitude adversarial vectors at both ends of every range;
   - one vector just beyond the frozen range, which must return `OVERFLOW`;
   - malformed maps, which must return `INVALID_MAP`.
5. **Static cost estimate.** Give a per-classification instruction or multiply count from the code structure, per node and per feature. This is an analytic estimate only; measured timing is RP0b.
6. **Write `FINDINGS.md`.** It should cover the width contract, results, any oracle/RTL divergence, and limits.

### 4. Verification commands

```bash
timeout 60 bash -c 'ulimit -v 1048576; cc -std=c99 -O2 -Wall -Wextra -Werror -fno-fast-math research/som_rp0/bmu.c research/som_rp0/harness.c -o build/som_rp0/harness'
timeout 60 bash -c 'ulimit -v 1048576; python3 -B -I research/som_rp0/oracle_compare.py --harness build/som_rp0/harness'
# portability: cross-compile only, no flashing (skip with a recorded note if the toolchain is absent)
timeout 60 arm-none-eabi-gcc -std=c99 -O2 -mcpu=cortex-m33 -mthumb -Wall -Werror -c research/som_rp0/bmu.c -o build/som_rp0/bmu_m33.o
git diff --check -- research/som_rp0 spu_strategy/contract_som_rp0_2026-10-20.md
```

### 5. Stop conditions

- The RTL and oracle overflow semantics disagree → **HALT**, report, and do not pick one silently.
- The frozen ranges need 128-bit comparison and no portable exact implementation fits within scope → **HALT** and propose a narrower profile.
- Any oracle mismatch that isn't an overflow refusal → **HALT**; do not adjust the oracle to match.
- Stop when RP0a is complete. Do not begin RP0b.

---

## Tranche RP0b — on-device timing, Class C (outline only, NOT authorized)

This tranche needs separate explicit owner authorization, with a frozen attempt budget,
per the bench-evidence discipline and AGENTS.md §4.2/§4.3. Planned shape:

- **Placement.** The BMU runs on core 1, from SRAM, not flash/XIP. A PIO+DMA synthetic sensor stream, with sequence numbers and PIO-counter timestamps, feeds a ring buffer. **Southbridge traffic runs at the same time**: SPI command streaming plus USB console.
- **Measurement.** Worst-case classification latency over N ≥ 10 runs. Count dropped, late and corrupt frames from sequence numbers and CRC, and record southbridge transaction integrity.
- **Positive control.** A deliberately overloaded configuration must show dropped frames, so that "zero drops" is meaningful.
- **Packet:** timestamp, frame id, prototype-set hash, feature-extraction version, best node, exact distance and gap, ambiguous/unfamiliar flags (unfamiliar = exact squared-distance threshold), and status.
- **Acceptance.** Classification completes within a declared budget, with zero frame or southbridge corruption, and the exact outputs match the RP0a host build for identical inputs.
- **Storage.** SD logging of raw frames is asynchronous, outside the acquisition and command paths, and record stalls explicitly.
