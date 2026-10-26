# GPU hardware campaign template

Copy this file to
`spu_strategy/contract_gpu_<feature>_<date>.md`. Fill every field and review
the frozen inputs and stop conditions before hardware execution. Store evidence
under a new `build/gpu_campaign/<campaign-id>/` directory. Use
[`docs/GPU_BRINGUP_RUNBOOK.md`](../docs/GPU_BRINGUP_RUNBOOK.md) for the
standard T1G recovery path.

## 1. Objective and acceptance

```text
Campaign ID:
Owner:
Spec author:
Implementer:
Auditor:
Objective (one sentence):
Baseline acceptance:
Candidate acceptance:
Stop when:
```

Name the exact operator observation or software gate that constitutes success.
Keep operator observation, captured pixels, internal telemetry, simulation,
and build evidence as separate claims.

## 2. Frozen inputs and known-working baseline

| Input | Exact identity | SHA-256 / revision | Evidence path |
|---|---|---|---|
| Board and FPGA | | | |
| Baseline bitstream | | | |
| Source checkout and build inputs | | | |
| Pin map, clocks, harness | | | |
| Transport and device path | | | |
| Packets and fixtures | | | |
| Sender and analysis tools | | | |
| Expected baseline observation | | | |

Default Wukong recovery baseline:

```text
image: build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
SHA-256: e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5
source checkout: build/t1f_clean_qualification_20260922
source commit: a64d87c7ae0d96b44d8178c20f2421376a975ac0
recovery: load to SRAM, then send the frozen A/B/C packets and observe each
```

## 3. One-change hypothesis

```text
Single change under test:
Files or build inputs changed:
Expected effect:
Observation that would falsify the hypothesis:
Focused software checks and exact commands:
Expected outputs:
Rollback point:
```

Do not bundle unrelated changes. Reuse passed gates while their inputs remain
hash-identical. Label a rebuilt image `RECONSTRUCTION` unless its historical
build inputs are fully established.

## 4. Allowed work and fixed budget

```text
Autonomous offline work allowed:
Allowed software/helper repairs:
Hardware actions allowed:
Maximum hardware attempts:
Maximum wall time per attempt:
Maximum cumulative hardware time:
Maximum SRAM loads:
Maximum scene sends / packets per attempt:
Maximum analyzer captures and duration:
Maximum resets:
Maximum board power cycles:
Maximum wiring changes:
```

Routine repairs within this scope and budget do not require renewed approval.
Obtain one operator-readiness report before each physical attempt, not before
every command or packet. A started attempt consumes a slot even if it fails
or becomes unavailable. A new objective, image identity, protocol, pin/clock
change, acceptance change, or exhausted budget requires renewed owner
authorization. When acceptance is met, close the campaign immediately; unused
budget does not authorize extra experiments.

## 5. Command-first procedure and checkpoints

Use a fresh directory for every attempt. Execute the standard baseline path
first:

```text
1. Preflight board, monitor, wiring, serial identity, and frozen hashes.
2. Detect the expected FPGA; load the exact baseline to SRAM.
3. Record IDCODE, load status, and monitor signal lock.
4. Send one frozen scene packet; preserve its transcript.
5. Observe and record the screen before sending the next packet.
6. After a candidate failure, replay the known-working baseline before further diagnosis.
```

| Attempt | Phase | Input hash | Exact command / report path | Result | First failed boundary |
|---:|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

Classify only the first failed boundary:

```text
preflight/device | programming | signal lock | host transport |
FPGA receipt | scene activation | rendering/display | NOT MEASURED
```

Record each operator observation with UTC time, scene/phase, image summary,
signal lock and operator intervention. A passing host write does not prove
FPGA receipt. Static configuration readback does not prove fresh runtime
state. Preserve raw evidence before interpreting it.

## 6. Recovery and stop rules

```text
First failure -> preserve raw evidence -> identify first failed boundary
              -> choose one bounded correction -> recheck known-good baseline
              -> resume only within the frozen budget
```

Do not make blind retries or change multiple causes at once. Stop for unsafe
power/heat, unknown wiring or pin identity, repeated loss of the expected
device, flash-write requirement, budget exhaustion, or a required change to
frozen acceptance, protocol, pins, clocks or image identity.

## 7. Closeout

```text
Objective status: COMPLETE | FAILED | BLOCKED | BUDGET EXHAUSTED
Last known-good artifact and hash:
Current loaded artifact:
Acceptance evidence:
Unmeasured boundaries:
Attempts/actions used and remaining:
First concrete regression boundary (if found):
Next authorized action:
```

Do not claim silicon verification without a corresponding entry in
`docs/hardware_evidence.md`. Otherwise label the result `operator-observed`,
`testbench-verified`, `simulation-only` or `unmeasured`, as appropriate.
