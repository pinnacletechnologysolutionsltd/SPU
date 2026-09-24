# Engineering Contract: T1g Temporal Prepared-Scene Replacement

**Date:** 2026-09-23<br>
**Contract ID:** `GPU-T1G-TEMPORAL-SCENE-REPLACEMENT-2026-09-23`<br>
**Revision:** 1<br>
**Status:** `Q2 PASS — THREE-SCENE FIRST-FRAME QUALIFICATION`
**Owner:** John Curley

## 1. Objective

Qualify deterministic, tear-free replacement of a four-primitive prepared
scene across three frozen scenes:

```text
scene A -> scene B -> scene C
```

This tranche qualifies temporal scene replacement using the existing T1f
active/candidate banks, four-result preparation, and frame-boundary activation.
It does not redesign the renderer or UART protocol.

T1d D3 remains separately classified:

```text
INFRASTRUCTURE FAIL — FX2 sustained-stream limitation
```

T1f remains closed as operator-observed physical visual evidence.

## 2. Frozen T1f boundaries

The following remain unchanged:

```text
PREPARED_SCENE=1
FOUR_PRIMITIVE_SCENE=1
252-bit primitive record
1008-bit scene
126 payload bytes
127 wire bytes including A5
115200 8N1
smaller signed depth = nearer
equal depth = lower primitive identity wins
background when no primitive is valid
25 MHz pixel-domain renderer
no framebuffer
no new render clock
```

No transport framing, baud, record layout, depth semantics, or acceptance
criteria changes are authorized by this contract.

## 3. Existing source findings

The current implementation already provides the intended basic mechanism:

```text
hardware/rtl/gpu/spu_scene_loader.v
    active and candidate scene banks
    candidate remains invisible during receipt
    complete candidate sets commit_pending
    bytes are ignored while commit_pending is asserted

hardware/rtl/gpu/spu_prepared_scene_control4.v
    all four derived depth results must match one candidate generation
    activation requires commit_pending, readiness, and frame_start

hardware/rtl/gpu/spu_gpu_top.v
    coverage and depth state are re-anchored from the activated scene
    at frame_start
```

No production RTL edit is implied by Q0 or Q1.

## 4. Q0 — Update-semantics review

Q0 shall freeze the behavioral target and scene definitions without creating
or modifying fixture files. The scene identities are:

```text
scene A = fixtures/gpu_t1f_scene_wire_127b.hex (existing T1f main scene)
scene B = fixtures/gpu_t1f_coverage_scene_wire_127b.hex (existing T1f coverage scene)
scene C = a new semantic scene specification; fixture generation is deferred
          until Q1 closes
```

Scene C is defined from scene A by translating all four triangle geometries
eight screen pixels right and eight pixels down. Preserve every primitive's
RGB and affine depth ordering, including equal-depth relationships. For a
depth plane `z(x,y)=A*x+B*y+C`, translate its constant term to
`C' = C - 8*A - 8*B`, so corresponding translated pixels retain the same
depth. Scene C therefore distinguishes geometry motion while preserving the
scene A winner semantics.

The representative scene C samples are the corresponding scene A samples
translated by `(8,8)`: `(28,28)`, `(68,28)`, `(38,68)`, `(58,68)`, and
`(48,48)` for primitive-0 through primitive-3 winners and the equal-depth
record-0 tie. Their expected RGB values are respectively red, green, blue,
yellow, and red. `(13,13)` is the translated background sample and remains
black. These are required to be valid active pixels in the frozen renderer
profile.

The representative pixels for scene A are `(5,5)` black, `(20,20)` red,
`(60,20)` green, `(30,60)` blue, `(50,60)` yellow, and `(40,40)` red for the
equal-depth record-0 tie. For scene B they are `(40,40)` black, `(20,20)` red,
`(60,20)` green, `(20,60)` blue, and `(60,60)` yellow.

Frame numbering starts at zero on reset deassertion and increments at each
`frame_start`. The initially black scene remains visible until scene A
activates. Scenes B and C are transmitted only after the preceding scene's
activation and loader re-acceptance have been established by the Q1 frozen
delay. For each candidate, the activation frame is the first `frame_start`
after all four derived results are ready and generation-matched; the prior
scene remains active through the preceding frame.

Record the existing fixture hashes:

```text
scene A SHA-256 (hex file): abf881178c4384f9210575aa2992c784cb6e19fcd10f149b81631e39591c8fda
scene B SHA-256 (hex file): 80bb103e43e1fc06a98e1d03166a673b35ea4e70c1c2b5fd34ff2caf177fb607
```

Q0 shall not generate or modify fixtures; the T1d fixture remains immutable.
Q1 may generate the Scene C fixture only after pacing and activation semantics
are frozen.

Q0 shall also freeze:

1. scene A/B fixture identities and hashes, plus the semantic definition of
   scene C (its fixture identity and hash are deferred until Q1 generation);
2. predetermined representative pixels and expected colors for each scene;
3. the rule determining each scene's activation frame;
4. the rule that the previously active scene remains visible for complete
   frames while the next candidate is received and prepared;
5. the rule that a candidate cannot become visible before a frame boundary;
6. the rule that no frame may contain a mixture of two scene identities;
7. the exact behavior when input arrives while `commit_pending` is asserted;
8. the minimum testbench observability needed to distinguish scene identity,
   candidate state, readiness, activation, and frame number.

For this contract, a frame is mixed if any active pixel is rendered using
primitive data from more than one scene identity. The outgoing scene remains
active through the frame in which the complete candidate is received and
prepared. The candidate becomes active only at the first `frame_start` for
which all four candidate results are ready and generation-matched; that
frame's first active pixel and all later pixels use the new scene. Testbench
observability shall record the active and candidate raw scene values, loader
`receiving`/`commit_pending` and payload count, four prepared readiness bits
and generation match, `activate_scene`, `frame_start`, and a monotonically
counted frame number.

Q0 shall use the existing source and T1f test structure. It shall not modify
RTL, XDC, bitstreams, UART timing, or physical fixtures.

## 5. Q1 — Host-pacing characterization

Q1 shall measure, in the top-level simulation path, the interval from:

```text
final UART payload byte accepted
    -> four derived depth results ready
    -> next eligible frame_start
    -> activation
    -> commit_pending cleared
```

While `commit_pending=1`, incoming UART bytes are not accepted. The physical
path exposes no ready/ACK indication, so T1g shall not claim arbitrary
back-to-back scene delivery. Q1 shall characterize a conservative host-side
inter-scene delay that guarantees the prior scene has completed preparation,
frame-boundary activation has occurred, and the loader is accepting bytes
again.

The bound shall include the worst-case frame phase, not an average preparation
time or merely the 126-byte UART duration plus preparation time:

```text
last byte received
 -> four depth preparations complete
 -> wait up to one full frame for frame_start
 -> activation and commit_pending clear
 -> characterized margin
```

The result shall be reported in:

```text
clk_pixel cycles
frame periods
115200-baud wall-clock equivalent
```

Q1 shall establish a frozen safe inter-scene interval with a recorded margin.
The interval shall be sufficient for:

```text
send A
wait safe interval
send B
wait safe interval
send C
```

No assumption that the UART accepts arbitrary back-to-back scenes is allowed.

### Q1 measured result

The top-level phase characterization used an 8,858-cycle frame and measured
final-byte-to-four-result-ready as 95 `clk_pixel` cycles for all five sampled
transitions, including a transition to generated scene C. Final-byte-to-
`commit_pending` clear was 8,854, 8,864, 4,430, 5,907, and 101 cycles for
final-byte phases 5, 8,853, 4,429, 2,952, and 8,758 respectively. Activation
occurred only at the next frame boundary. The measured values include a
negedge observation quantization of at most one cycle.

The production VGA frame is 800 × 525 = 420,000 `clk_pixel` cycles. The
conservative busy bound is frozen as one complete production frame plus the
measured preparation latency:

```text
420,000 + 95 = 420,095 clk_pixel cycles = 16.8038 ms at 25 MHz
```

Freeze a minimum host wait of **20 ms after the final payload byte has been
accepted and before sending the next scene's `A5` byte**. This gives 3.1962 ms
margin over the conservative busy bound. A 127-byte 115200 8N1 transaction
takes 11.0243 ms, so the minimum scene-start-to-scene-start interval is
31.0243 ms when the host waits 20 ms after each completed transaction. The
scene C fixture may now be generated from the frozen Q0 specification.

Scene C was generated after freezing this pacing rule using:

```text
python3 tools/generate_gpu_t1g_scene_c.py
```

Generated fixture identity:

```text
fixtures/gpu_t1g_scene_c_wire_127b.hex
hex-file SHA-256: 5aad8b1b1954875ea78fb11192d94a19652e027aea8f33e1656ec950b50abca5
decoded 127-byte wire SHA-256: 863585de89f3a827e25d12ba262f35dafab93ba05440377fd56cc0f255a3ef7b
```

Q1 qualification ran:

```text
python3 software/tests/test_gpu_t1g_pacing.py
```

Result: PASS for final-byte phases immediately after frame start, immediately
before frame start, mid-frame, and two additional phases; all five transitions
preserved exact active-scene identity through activation. The pacing behavior
needed no transport or loader RTL change. The separate activation-state audit
below did require a top-level RTL correction, so T1g now requires a fresh B1
build after Q3 and cannot use the older T1f bitstream for T1g H1.

### Activation-state audit and localized correction

Source tracing confirmed that `spu_depth_dispatch4` returns each candidate
lane's `A_z`, `B_z`, `C_z`, `frac_bits`, and one-cycle `ready`; control4 records
all four results and only activates with all four ready bits from the current
candidate generation. At activation, control4 commits all four coefficient
and fraction tuples, consumes `ready_seen`, and returns to idle.

The top-level attribute handoff had one mismatch: lanes 0 and 1 selected the
candidate A/B/C coefficients during `activate_scene` but kept the outgoing
scene's `active_frac_bits`. Lanes 2 and 3 already muxed candidate fractions.
The T1f main and coverage scenes exercise the mismatch with fractional widths
28 and 24. `spu_gpu_top.v` now selects `frac_bits0/1` during activation for
lanes 0 and 1, matching the existing lanes 2 and 3 behavior. No interface,
transport, scene format, or raster RTL changed.

The activation-state assertions in `software/tests/test_gpu_t1g_pacing.py`
check differing old/new fractional widths in all four lanes, candidate
coefficient/fraction selection on the activation edge, all-four readiness and
generation match, committed active tuples, and readiness consumption. They
pass alongside all five pacing-phase transitions.

The focused regressions passed:

```text
spu_t1f_profile_tb.v             PASS (199 checks)
spu_t1f_top_oracle_tb.v           PASS (T1f-I2 four-way oracle)
spu_prepared_scene_banking_tb.v   PASS (876 checks)
software/tests/test_gpu_t1g_pacing.py PASS (pacing plus activation-state audit)
```

Q2 is now authorized to add three-scene visual and no-mixed-frame
qualification. The Q2 result is recorded below.

### Q2 — Three-scene first-frame qualification

The top-level simulation sent A, B, C, and A again, exercising five
transitions across five final-byte phases. For each transaction it checked the
old active raw scene and all four active `A_z/B_z/C_z/frac_bits` tuples stayed
stable during receipt and preparation; activation required all four ready
results from the matching generation at `frame_start`; and the committed raw
scene and all four derived tuples changed together.

The first complete 80×100 active frame after each activation was checked at
every pixel against a direct edge-coverage/depth evaluation of that frame's
fixture geometry and the candidate-derived depth tuple. During all 40,000
sampled pixels, the active raw scene and all four per-pixel derived parameter
tuples remained fixed to the activated scene. Results:

```text
scene B first frame: 8,000 / 8,000 pixels PASS
scene A first frame: 8,000 / 8,000 pixels PASS
scene B first frame: 8,000 / 8,000 pixels PASS
scene C first frame: 8,000 / 8,000 pixels PASS
scene A first frame: 8,000 / 8,000 pixels PASS
mixed-scene pixels: 0
```

Command:

```text
python3 software/tests/test_gpu_t1g_pacing.py
```

Result: `PASS: T1g pacing characterization FRAME_CYCLES=8858`.
This closes simulation Q2 for the frozen fixtures and small-frame test
profile. It does not qualify physical VGA behavior.

If the safe interval cannot be established without a protocol handshake,
FIFO, queue, or RTL change, HALT and classify that as a separate transport
tranche.

## 6. Required Q0/Q1/Q2 invariants

For each transition A→B and B→C:

```text
old scene remains active during incomplete receipt;
old scene remains active during derived-state preparation;
new scene activates only at frame_start;
all four derived results belong to the new scene;
the first new frame is internally coherent;
no mixed scene frame occurs;
the active scene remains stable until the next qualified activation.
```

## 7. Out of scope

This tranche shall not:

* add UART acknowledgements or ready/flow-control signals;
* add a FIFO, packet queue, or packet resynchronization;
* alter the `A5` wire protocol;
* change baud or UART timing;
* add a framebuffer;
* implement B2 context scheduling;
* modify rasterization, depth comparison, or VGA timing;
* launch synthesis, program an FPGA, or transmit physical UART data;
* claim dynamic hardware behavior before physical qualification.

## 8. Halt conditions

HALT if:

* scene identity cannot be observed unambiguously;
* activation can occur away from `frame_start`;
* active state changes during candidate receipt or preparation;
* any mixed-scene frame is observed;
* derived state does not match the activated raw scene;
* input loss while `commit_pending` prevents a useful bounded pacing rule;
* a protocol or RTL change is required;
* existing T1f behavior regresses.

## 9. Execution ladder

```text
Q0  update-semantics review and semantic scene freeze (no fixture generation)
    ↓
Q1  pacing characterization and safe-interval freeze
    └─ generate Scene C fixture from the frozen Q0 semantic specification
    ↓
Q2  three-scene simulation qualification
    ↓
Q3  clean repository qualification
    ↓
B1  Artix build qualification, required because T1g changed RTL
    ↓
H1  bounded physical frame-transition demonstration
```

Q0, Q1, and Q2 are source-review/simulation stages. Q3 and B1 are complete.
H1 is recorded below as an operator-observed physical demonstration.

### H1 — Bounded physical frame-transition demonstration

The T1g B1 image was loaded into SRAM after a board power cycle:

```text
command: openFPGALoader -c dirtyJtag --freq 1000000 \
         build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
result:  Load SRAM 100%, isc_done 1, init 1, done 1
bitstream SHA-256:
e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5
```

The frozen host sender transmitted A→B→C with a 3-second dwell per scene,
20 ms post-drain delay, and minimum 31.1 ms start-to-start pacing. Each
127-byte transaction completed `tcdrain`; measured start-to-start intervals
were 3006.081843 ms and 3005.912119 ms. The transcript is
`build/t1f_clean_qualification_20260922/build/t1g_h1_20260923/uart_sequence_attempt_03.json`.

The operator observed both scene changes on the monitor and reported no
visible yellow shimmer during this run. This is an operator-observed physical
demonstration, not a frame-captured measurement. Earlier logic-analyzer
captures used the wrong PMOD and are excluded from H1 evidence; correcting
the PMOD connection restored the display. Simulation Q2 remains the pixelwise
evidence for first-frame coherence.

Result: **H1 PASS — bounded A→B→C transitions observed at the frozen pacing**.

## 10. Current authorization

```text
Q0 = PASS — SEMANTICS FROZEN
Q1 = PASS — PACING FROZEN; SCENE C GENERATED
Q2 = PASS — THREE-SCENE FIRST-FRAME QUALIFICATION
Q3 = PASS — CLEAN REPOSITORY QUALIFICATION
B1 = PASS — ARTIX-7 100T BUILD AND SRAM LOAD
H1 = PASS — OPERATOR-OBSERVED A→B→C; NO VISIBLE SHIMMER IN LATEST RUN
```
