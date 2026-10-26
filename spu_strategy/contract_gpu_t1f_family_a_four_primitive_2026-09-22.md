# Engineering Contract: T1f Family A Four-Primitive Prepared Scene

**Date:** 2026-09-22<br>
**Contract ID:** `GPU-T1F-FAMILY-A-FOUR-PRIMITIVE-2026-09-22`<br>
**Revision:** 4<br>
**Status:** `H1 PASS — OPERATOR-OBSERVED VISUAL EVIDENCE`<br>
**Owner:** John Curley

## 1. Purpose

Implement and qualify a bounded four-primitive prepared-scene compositor using
Family A: four parallel streaming primitive lanes at the existing 25 MHz pixel
clock.

This contract does not implement the B2 context-managed architecture. B2 is a
deferred scalable follow-on. B1 and the framebuffer family are out of scope.

T1d and T1e evidence remain immutable. T1d D3 remains:

```text
INFRASTRUCTURE FAIL — FX2 sustained-stream limitation
```

T1e remains physically demonstrated at the visible output level.

## 2. Objective

Extend prepared-scene mode from two to four triangle records while preserving:

```text
one completed VGA pixel per clk_pixel
clk_pixel target = 25 MHz
smaller signed depth = nearer
equal depth = lower primitive identity wins
background if no primitive is valid
atomic scene activation at a frame boundary
```

The existing direct two-triangle input mode and the frozen 64-byte T1d/T1e
fixture shall remain unchanged and regression-covered.

### 2.1 Prepared-scene profile selection

The existing prepared-scene selector has a frozen two-primitive meaning and
cannot be widened by runtime packet-length inference. Profile selection is
therefore compile-time only:

```text
PREPARED_SCENE=1, FOUR_PRIMITIVE_SCENE=0
    existing T1d/T1e profile: 504-bit scene, 63 payload bytes

PREPARED_SCENE=1, FOUR_PRIMITIVE_SCENE=1
    T1f Family A profile: 1008-bit scene, 126 payload bytes
```

`FOUR_PRIMITIVE_SCENE` defaults to `0`. No runtime wire-format inference is
permitted. `A5`, UART framing, baud, record layout, direct-path behavior, and
the existing T1d/T1e fixtures remain unchanged.

## 3. Frozen four-primitive format

The existing 252-bit triangle record is retained unchanged:

```text
252 bits per primitive
1008-bit four-primitive scene
126 payload bytes
127 wire bytes: A5 start byte + 126 payload bytes
115200 8N1 UART framing
```

The existing `fixtures/gpu_t1d_scene_wire_64b.bin` shall not be modified or
repurposed. T1f shall add a separately named generated fixture after the
simulation oracle is frozen.

No CRC, resynchronization, baud, or UART timing redesign is authorized by this
contract.

## 4. Scope

### In scope

* expand prepared-scene storage and unpacking to four records;
* retain two-bank atomic raw-scene storage;
* generalize setup-time depth preparation to four jobs using the existing
  shared depth arithmetic;
* instantiate four parallel coverage/depth lanes in prepared-scene mode;
* reduce four valid fragments deterministically by signed depth;
* preserve lower-primitive-identity tie behavior;
* add focused simulation and a four-primitive top-level oracle;
* run repository qualification;
* synthesize and place-and-route a uniquely identified Artix-7 artifact;
* perform one separately authorized visual hardware demonstration.

### Out of scope

* B2 serialization or retained-context scheduling;
* a new render clock or MMCM/PLL;
* a framebuffer or persistent depth/color store;
* external memory;
* moving geometry or per-frame scene updates;
* texture mapping, perspective correction, or rasterizer redesign;
* changes to the T1d/T1e fixture or acceptance criteria;
* FX2 telemetry or reopening T1d D3;
* UART baud/framing changes;
* optimization before functional qualification.

## 5. Compatibility boundary

The existing two-primitive direct-input path shall remain behaviorally and
interface compatible unless a separately reviewed contradiction is found.

The four-primitive expansion is authorized only for `PREPARED_SCENE=1`. The
existing direct `tri0`/`tri1` ports remain the legacy two-primitive path.

Any top-level interface change, transport reinterpretation, or change to the
existing direct path requires HALT and amendment.

## 6. I0 — implementation preflight

Before editing production RTL, record exact source anchors for:

```text
four-record scene bank width and payload counter
active/candidate unpack mapping
four coverage lanes
four depth accumulators
shared depth-setup dispatch
four-result readiness and generation matching
four-way winner reduction
frame-boundary activation
```

Freeze the resource/timing guard before implementation. The guard shall be a
reviewed envelope, not an arbitrary percentage chosen after the build:

```text
clk_pixel post-route Fmax must be >= 30.00 MHz
sys_clk post-route Fmax must be >= 50.00 MHz
no unconstrained or ignored clock/pin constraint may be introduced
device resources must remain within XC7A100T capacity
```

I0 freezes the following rationale-based maximum absolute ceilings for this
Family A implementation probe:

```text
SLICE_LUTX: 30,000
SLICE_FFX:  10,000
CARRY4:        800
DSP48E1:         4
RAMB18E1/RAMB36E1: 0
```

These ceilings are grounded in the T1e baseline and the authorized structural
change: two additional streaming primitive lanes, four-way reduction, and
four-record scene/control state while retaining one shared depth-math engine.
They are intentionally absolute ceilings, not arbitrary percentage targets.
The 30 MHz pixel-clock floor leaves a reviewed 5 MHz margin above the required
25 MHz display rate while allowing the added lane logic to consume part of the
T1e 42.02 MHz measured margin. Exceeding any ceiling is an I0/B1 HALT for
architecture classification, not permission to optimize blindly.

No implementation is authorized if the four-lane path requires a new clock,
framebuffer, or direct-path interface change.

## 7. I1 — Family A implementation

Implement the minimum prepared-scene-only change:

1. Expand `spu_scene_loader` to two 1008-bit banks and a payload counter that
   accepts exactly 126 payload bytes after `A5`.
2. Preserve the existing byte-to-record bit mapping for each 252-bit record.
3. Extend candidate/active scene control to four depth-preparation results.
4. Retain one shared setup-time depth-math engine unless a measured defect
   requires review.
5. Provide four coverage lanes and four registered depth accumulators.
6. Implement a deterministic four-input reduction using valid coverage,
   signed depth, and primitive identity.
7. Preserve frame-boundary activation and old active-scene retention while a
   candidate scene is incomplete or being prepared.

No production RTL edit is permitted before I0 is reviewed.

## 8. I2 — simulation qualification

Create a new four-record fixture and oracle. The T1d/T1e 64-byte fixture must
remain byte-for-byte unchanged.

The oracle shall include at least:

```text
background pixel
primitive-0-only pixel
primitive-1-only pixel
primitive-2-only pixel
primitive-3-only pixel
overlap won by primitive 0
overlap won by primitive 1
overlap won by primitive 2
overlap won by primitive 3
equal-depth tie
```

At least three distinct primitive identities must win across the scene. For
unequal-depth permutation tests, the same geometric primitives, depths, and
colours shall be permuted among record slots; the visible winner must remain
the nearest geometric primitive. Equal-depth cases are excluded from this
permutation invariant and shall independently select the lower record
identity.

The top-level simulation shall verify:

```text
complete 127-byte wire reconstruction
incomplete scene does not activate
all four derived depth results are ready before activation
activation occurs only at frame_start
active scene remains stable while a candidate is received/prepared
background and all four coverage cases
depth order and tie semantics
```

Any mismatch is a classification failure. Do not alter behavior to make the
oracle pass under this contract.

## 9. I3 — repository qualification

From a clean source state, run:

```bash
TB_FILTER=gpu python3 run_all_tests.py
bash tools/verify_repo.sh
```

Run the focused four-primitive top-level oracle separately and preserve all
outputs, source commit, dirty-state record, and fixture hashes.

I3 may close as `PASS WITH UNRELATED GATE DEBT` when all of the following are
true:

```text
the clean T1f qualification snapshot is established;
all T1f-specific profile, banking, and top-level oracle tests pass;
the full repository gate is executed;
every full-gate failure is classified and demonstrated unrelated to the T1f
source closure; and
the unrelated failures are preserved as repository-health debt.
```

This classification does not claim full repository health and does not mark
the unrelated failures resolved. It permits T1f B1 preflight/review to
continue; B1 still requires separate authorization.

## 10. B1 — Artix-7 build qualification

Before launch, freeze:

```text
artifact tag
exact build command
source commit and clean-state requirement
A7 seed and frequency
tool and chipdb provenance
timing constraints and slack interpretation
resource guard from I0
warning and unconstrained-path policy
bitstream SHA-256 evidence
```

The Artix build-flow profile is:

```text
FOUR_PRIMITIVE_SCENE=0|1, default 0
T1F_B1_S1 requires GPU_T1D_UART=1 and FOUR_PRIMITIVE_SCENE=1
T1D/T1E tags retain FOUR_PRIMITIVE_SCENE=0 behavior
```

The selector is passed through the UART-enabled GPUVGA Yosys elaboration to
`spu_a7_gpu_vga_top` and then to `spu_gpu_top`. Runtime wire-format inference
is not introduced.

The build must use the existing 25 MHz Artix-7 VGA path and no new clock
source. A generated bitstream is not sufficient for B1 PASS.

## 11. H1 — physical visual demonstration

H1 requires separate authorization after B1 PASS.

Use:

```text
the exact B1-qualified bitstream
the new 127-byte four-primitive fixture
the existing qualified 115200 8N1 UART path
the corrected qualified VGA pinout and cable
```

Before transmission, establish the black/unarmed locked baseline. Ordinary
procedural or infrastructure recovery is permitted before meaningful DUT
stimulus, consistent with EXPLORE workflow rules. Once the UART preflight
passes, the qualified four-primitive transaction is single-shot: send the
fixture exactly once. No analyzer telemetry is required.

## 12. Acceptance

### PASS

All four primitives compose correctly in simulation, T1f-specific repository
tests pass, every full-gate failure is classified as unrelated repository
debt, the Artix build closes the frozen timing/resource guard, and the bounded
physical image matches the predetermined oracle.

### FAIL

A deterministic simulation or physical result differs from the frozen oracle,
or the implementation changes existing two-primitive semantics.

### INFRASTRUCTURE FAIL

Required build, programming, UART, or VGA infrastructure prevents execution.

### INCONCLUSIVE

The physical observation cannot distinguish correct four-primitive depth
composition from another explanation.

## 13. Mandatory halt conditions

HALT if:

* B2, B1, framebuffer, or a new render clock becomes necessary;
* the direct two-primitive path changes unexpectedly;
* the four-record wire format cannot be frozen exactly;
* atomic four-result preparation cannot be established;
* primitive-order independence fails for unequal depths;
* tie behavior is unspecified or nondeterministic;
* a T1f-specific repository test fails;
* a full-gate failure is attributable to the T1f source closure or cannot be
  classified;
* timing/resource guard fails;
* bitstream or fixture provenance is ambiguous;
* physical output differs from the frozen oracle.

## 14. Current authorization

```text
I0 = COMPLETE — SOURCE/RESOURCE/TIMING PREFLIGHT PASS
I1 = COMPLETE — IMPLEMENTATION / PROFILE TESTS PASS
I2 = COMPLETE — TOP-LEVEL ORACLE PASS
I3 = PASS WITH UNRELATED GATE DEBT
B1 = PASS — BUILD/TIMING/PROVENANCE QUALIFIED
H1 = PASS — OPERATOR-OBSERVED VISUAL EVIDENCE
```

This revision records the I3 gate-debt amendment and the validated T1f
build-flow profile. B1 completed from clean source commit
`cd507cd0465b00bc827d88458c0013ff6cff5189` with bitstream SHA-256
`45fb9e4b22e13c1893df7f39d36a365c5f5d0db1d5e30443cbae9afcc30ba755`.
H1 programming and the single qualified UART transaction completed using that
bitstream and the frozen T1f fixture. The operator observed the expected
top-left four-triangle scene with red, green, blue, and yellow depth-winner
regions on a black background, including the red equal-depth primitive-0
tie. No logic-analyzer telemetry was used. The unrelated repository failures
and the prior T1d D3 analyzer limitation remain open and are not represented
as resolved.
