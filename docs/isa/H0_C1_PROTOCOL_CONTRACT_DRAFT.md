# H0-C1 — Minimum host-driven execution protocol: contract draft (revision 5)

**Status:** NON-NORMATIVE DRAFT for independent review. Nothing here is implemented, qualified, ratified or an encoding. Normative ratification and RTL implementation **HOLD**.
**Revision:** r5. Earlier revisions are in git history: r1 `ff98404134ae63bc481e9ea9d6dd4d3ad1398f8e`, r2 `96c75a6c8b447a4c7168ef5b75f4109d75d8e1db`, r3 `b7eddd84cf088b83504dbcf9f17aed65c55589c5`.
**Baseline identity for this revision:** `dev/next` at `cc257838811b5751a1314a5c71146457ed6924e8` (clean before editing). Existing VM, assembler and RTL sources are unchanged from public RC2 `b063280`.
**Language:** MUST/SHALL mark requirements of this *proposed* contract, not properties of the current design. Mechanisms described here are not claimed to exist in the RTL unless a source fact is cited. No instruction-set or mathematical change; no queue; no autonomous program counter; no unified FLAGS register; no counter width, SPI command value or bit position is assigned.
**Goal and limit.** One small Artix-7 execution profile that accepts only defined commands, executes them correctly, reports exactly what happened and never presents an invalid result as successful. It is not a protocol for every experimental subsystem. This alignment does not authorize implementation or normative ratification.

## 0. What changed

Independent reviews: r1 (`/tmp/H0-C1-independent-review-ff98404.md`), r2 (`/tmp/H0-C1-r2-independent-review-96c75a6.md`), and r3 (the Codex report text supplied in the working session, no stored file, plus a second review by the author). Reviews of r1 and r2 are stored outside the repository; no other review identifier exists. Source facts relied on in r4 were verified: the only reset source is the external `rst_n` pad through a synchronizer and counter (`spu_a7_top.v:153-176`), with no soft reset in the SPI slave or top; the core's `boot_done` input is tied to 1 (`:785`); an `0xA5` write with `sel=7` sets `torus_emit_enable` and `torus_idx` (`spu13_core.v:1867-1870`), after which the hydration sweep emits an autonomous Artery chord (`:1970`), and neither site is guarded by `ENABLE_TORUS`; the Padé coefficient memories have no reset branch; the low half of a coefficient pair is staged in an array and used when the high half arrives.

Owner decisions approved for r4:

| Issue | Decision |
|---|---|
| N1 reset provider | A documented **physical** reset mechanism for the first image; no soft-reset command; reset availability is a board-level qualification requirement. |
| N2 configuration targets | A strict allowlist of permitted configuration commands; all others rejected before any mutation. |
| B3 A31 refusal witness | Two frozen, identified configurations: SET-N (ordinary) and SET-R (deliberate refusal qualification). |
| B4 acknowledgement | Host-visible acknowledgement after each committed configuration write. |
| M1 identity | Hardware-checked canonical sequence against the manifest; a host-declared hash alone is insufficient. |
| M2 boundaries | Exact sampling points and same-cycle priorities (§5). |
| M3 aliasing | Reset-scoped identities, explicit host resynchronization, bounded-loss rules (§6). |
| M4 protected state | Partitioned by instruction, configuration and background ownership (§9). |
| M5 initialization | Configuration writes rejected during INITIALIZING, accepted in CONFIG_REQUIRED. |
| ROTC | Candidate angles `{0, 2, 5}` only; unqualified pending numerical and image evidence. |
| Numerical contract | Prepared by the author from source, independently reviewed by Codex, separate from H0-C1, non-normative until tested. |
| Integrity errors | Separate transport errors from arithmetic and integrity faults; no invented classification. |

## 1. Evidence base

| Source | What it establishes (as built) |
|---|---|
| [`ISA_V02_STATE1_FINDINGS.md`](ISA_V02_STATE1_FINDINGS.md) | The core acknowledges unsupported opcodes with `inst_done` and no effect; no success/refusal signal; different QR hydration and `QLDI` scales. |
| [`ISA_V02_H0TRANSPORT1_FINDINGS.md`](ISA_V02_H0TRANSPORT1_FINDINGS.md) | `0xB1` yields a one-cycle strobe with no queue or acknowledgement; `inst_done` not host-visible; silent drops; `0xAE` valid is sticky with no freshness. |
| [`ISA_V02_H0V1_FINDINGS.md`](ISA_V02_H0V1_FINDINGS.md) | Core-level simulation: overlapping strobes can swallow an instruction or lose an in-flight ROTC result; 40 opcodes acknowledged without effect on QR state (a QR-only check); boot-not-ready strobes lost; identical repeated results indistinguishable; the Padé sidecar rejects a busy request correctly. |
| [`ISA_V02_A31R2_FINDINGS.md`](ISA_V02_A31R2_FINDINGS.md) | Simulation: after an A31 inversion refusal the ordinary pipeline and core bridge publish the previous result (or `x`) with valid indications; one zero-divisor witness (denominator constant `2CEE24B2, 0, 0, 1`, higher coefficients 0). |

## 2. Initial profile (provisional name): SPU-H0-RPLU2-v0.2

Proposed profile requirements, not a claim that the current RTL enforces them or that any image has been built or qualified.

| Item | Decision |
|---|---|
| Device | Artix-7 XC7A100T |
| Execution | Host-driven, one outstanding instruction across the whole engine |
| Core configuration | `spu13_core` with the RPLU2 pipeline enabled; `ENABLE_MATH` enabled (ROTC requires it) |
| Disabled | REGEN, legacy core SOM (`ENABLE_CORE_SOM`), IROTC, Surd extension, RPLU2 extension bundle (JSCR/NSA) |
| Other peripherals | Every enable not listed here is off in the profile image (GPU, I2S, torus, lattice, SDRAM, gatekeeper and so on); the image's full parameter set is recorded in its build manifest |
| Excluded sidecars | Lucas, SU3, Neuro, live-evaluator and Padé-sidecar spins (coreless spins also tie `boot_ready` low) |
| Not present | Scalar registers, PC, call stack |
| **Supported** | QLDI (`0x1D`), QSUB (`0x1B`), ROTC (`0x1C`) with an angle in the profile's angle set, RPLU2 start (`0x2A`, including the pipeline's internal SOM, BTU and Padé stages) |
| **Unsupported** | Every other opcode, a ROTC angle outside `{0, 2, 5}`, and any noncanonical lane or reserved-field encoding |
| Excluded semantics | DELTA, HEX, REGEN, IROTC, SOM, Surd, SU3, Lucas, Neuro |
| Configuration | Exactly two frozen manifests, SET-N and SET-R (§3) |
| Reset | Existing physical reset pad only (§3, R-1) |

**Current-implementation gaps against the profile (source facts).** (a) No existing named Artix-7 spin has this configuration: the `RPLU2` spin sets `ENABLE_MATH` to 0 (ROTC would hang); `MULTIMEDIA` and `FULL` carry GPU/I2S (and SOM in `FULL`). (b) `spu_a7_top.v` does not pass `ENABLE_REGEN`, which defaults to 1. (c) `fpga_chain u_chain` is instantiated outside the `ENABLE_REGEN` generate (`spu13_core.v:1107` versus `:1134`) and is driven by a strobe computed from QLDI, QSUB and ROTC acceptance; disabling REGEN at the top alone does not establish the chain is absent or inert. (d) Whether the configuration closes timing is unknown. An alternative, **not approved**, if the configuration verifier proves disproportionately expensive: freeze the coefficients directly into a dedicated H0 qualification image.

**ROTC angle set.** Angles `{0, 2, 5}` are the initial **candidate** set, not a qualified one. Divide-by-three rotations, including angles 1, 3 and 4, are outside the initial H0 scope. The ledger records ROTC 0-5 silicon in two places with different scopes: a Wukong Artix-7 ROBOTICS main-core smoke (§3.0) and a dedicated Tang 25K probe (§3.2g). Neither qualifies this image, its operand boundaries or this protocol; the RTL gate `ROTC_MAX_VERIFIED_ANGLE = 35` is a decode bound, not evidence. The numerical contract (§10) specifies the candidate mappings and qualification requirements. Angles outside the candidate set are UNSUPPORTED, classified before any side effect (a profile policy, not a globally ratified ISA rule).

## 3. Reset and configuration lifecycle

**Reset (R-1 to R-4).**
- **R-1** The first image uses the existing physical reset pad (`rst_n`, synchronized and held by a counter). **No soft-reset command is introduced.** Reset availability is a **board-level qualification requirement**: the actual Wukong board must provide a documented, reliable means of asserting it (a button or an external GPIO connection). This is to be verified, not assumed (D16).
- **R-2** Reset cancels any outstanding transaction; invalidates both records (§5); invalidates configuration authorization and discards staged coefficient halves and sequence progress; discards any frame in progress; and permits no late event from the cancelled engine.
- **R-3** After reset the host must re-establish synchronization and configuration (§6).
- **R-4** If the host cannot assert reset, automatic timeout recovery is **not guaranteed**: after a host timeout the engine may remain busy, rejecting submissions, until reset. A host timeout is therefore **UNKNOWN OUTCOME / RECOVERY REQUIRED**, never an architectural outcome and never an assumed successful reset.

**Lifecycle (concept; encoding undecided).**

`RESET → INITIALIZING → CONFIG_REQUIRED → CONFIG_VALID(set) → READY`

- **CFG-1** Reset invalidates the configuration-valid state *even if physical configuration registers retain values*. The existing RTL does not reset the Padé coefficient memories; this contract never assumes asserting reset produces known coefficients.
- **CFG-2** **INITIALIZING** (boot and QR-file hydration; the core's `boot_done` is tied high in the Artix-7 top, so it begins at reset exit): `0xA5` configuration writes are **rejected** (not-ready kind, sub-state INITIALIZING); instructions are rejected likewise. **CONFIG_REQUIRED:** `0xA5` writes are accepted subject to the allowlist and sequence rules below; instructions are rejected (not-ready, sub-state configuration-required).
- **CFG-3** **Transport-available versus execution-ready.** The SPI interface (configuration writes in CONFIG_REQUIRED, record and status reads at any time) remains usable while the engine is not execution-ready. Only instruction execution is gated by READY.
- **CFG-4 Allowlist.** Only configuration commands in the frozen manifests may be written. The allowlist operates on the **complete command identity**: selector, material field, address, and any applicable subfield, plus the expected data value where the manifest fixes it. An unsupported configuration write is **rejected before any mutation**: it alters no coefficient storage, no torus control (`sel=7`), no SOM state and no other implementation state, and it stages nothing. Rejection kind: unsupported configuration target (§8). Transport diagnostics (the rejection record, the CRC sticky) are the only permitted state updates.
- **CFG-5 Manifests.** SET-N is intended as the ordinary Padé configuration once qualified; its contents are not yet frozen. SET-R is a deliberately constructed set containing the known zero-divisor witness; it is an explicitly identified **qualification mode**, not for general numerical use. Each manifest has a recorded identity and exact values (the ordered list of selector, address and value entries) and expected outcomes. The image need not support arbitrary switching during normal execution: changing set requires returning to CONFIG_REQUIRED, completing the full canonical sequence of the selected manifest, and establishing a new configuration identity.
- **CFG-6 Hardware-checked canonical sequence.** (1) Select one of the two manifests (how selection is expressed is open, D13a). (2) Require the manifest's prescribed ordered writes. (3) Compare selector, address and value of each accepted write with the manifest entry at the current progress position. (4) Advance progress **only after the corresponding write has committed**; a staged low half without its high half is not progress, and the committed record is compared in full. (5) Reject omissions, duplicates, unexpected values and misordered writes (rejection kind: configuration-sequence violation) and return to CONFIG_REQUIRED with progress cleared. (6) Invalidate configuration before any further instruction can be accepted if a later covered write would alter the established state. The transition to READY depends on successful completion of the selected manifest. An exact comparison against a small frozen manifest is the mechanism; no cryptographic engine is introduced; a host-declared hash alone is not accepted as identity.
- **CFG-7 Positive acknowledgement.** The host MUST be able to read, after each configuration write, an indication that the write **committed** (a progress position advanced), and the lifecycle state (INITIALIZING, CONFIG_REQUIRED with progress, CONFIG_VALID(set), READY). Waiting for it is bounded by a documented timeout; progress, rejection status and the reset indication (§6) are read before the next step. The existing RTL offers no such write-commit acknowledgement; it is an implementation requirement to be established in design, not an assumption.
- **CFG-8** Transfer is not mathematical validity: matching the manifest proves the intended values reached the intended registers, not that the values are numerically adequate (that is the manifests' own qualification, §10).
- **CFG-9** The manifests enumerate the runtime-writable state that influences `0x2A` (Padé numerator and denominator coefficients, relevant BTU rows, kappa, and any others, D14). Fixed SOM weights and other image constants are not runtime configuration; they are bound to the build identity.

## 4. Vocabulary, safety and liveness

> **Safety:** no accepted instruction produces more than one terminal outcome, and no refused or unsupported instruction publishes a fresh valid result.
> **Liveness (conditional):** an accepted instruction eventually completes, provided clocks continue, reset does not intervene and the profile's execution assumptions hold (§6).

| Term | Definition (proposed) |
|---|---|
| **Submitted** | A frame carrying an instruction word or configuration command reached the ingress. |
| **Transport-rejected** | Not delivered to the engine: CRC failure, malformed header, aborted frame. |
| **Rejected at acceptance** | Delivered but not taken: not execution-ready (any sub-state), a transaction outstanding, or a configuration target or sequence violation. |
| **Accepted** | Execution ownership transferred to the engine. CRC success is necessary, not sufficient. |
| **Completed** | The accepted transaction reached its terminal outcome and its record is published. |
| **Succeeded / Refused / Unsupported** | SUCCESS; REFUSED (execution ended without publishing an invalid result, e.g. A31 zero-divisor); UNSUPPORTED (opcode or operand outside the supported set; no effect). |
| **Result telemetry** | A host-visible result with a lane label; distinct from an architectural QR write (§7). |

`inst_done` MUST NOT be read as success. The existing port MAY remain as an internal completion input, with outcome, result and effect-commit timing supplied separately.

**Invariants (proposed).**

1. **INV-1** At most one terminal outcome per accepted instruction; none for a cancelled transaction.
2. **INV-2 Single outstanding, enforced by hardware**, from acceptance until the record is published and the effects are committed, across the core and everything behind the ingress. A second instruction is rejected visibly.
3. **INV-3 Rejected traffic is inert.** A rejected instruction or configuration write never alters, delays or discards an in-flight operation's step, result or record, including when the rejection coincides with a completion.
4. **INV-4 No fresh-valid on refusal.** REFUSED and UNSUPPORTED transactions raise no result-valid, commit or telemetry update and never present a previous result or an undefined value as fresh, including after reset; no late publication after cancellation.
5. **INV-5 Instruction authorization is classified and latched at acceptance.** One shared profile predicate checks the supported opcode, canonical lane indices, zero reserved fields, and for ROTC the supported candidate angle; it is evaluated once at acceptance and latched with the transaction. A CRC-valid instruction accepted while READY that fails this predicate completes as UNSUPPORTED, with no instruction side effects. Every instruction-caused initiation and side effect (the instruction-owned partition of §9) is gated by *that transaction's* latched authorization for its whole lifetime, not by the current incoming word. A later rejected word MUST NOT suppress or gate the accepted operation's execution, completion or publication.
6. **INV-6** Rejections are visible, distinct and fresh (§5, §8).
7. **INV-7** Consecutive transactions are distinguishable even with identical results.
8. **INV-8** A published record is stable until the next acceptance or reset, and its fields are mutually coherent.
9. **INV-9** Transport status is separate from arithmetic status.
10. **INV-10 Configuration immutability while busy.** Configuration writes are accepted only while no transaction is outstanding; otherwise rejected visibly (configuration-while-busy) and nothing is written.
11. **INV-11 Publish after commit.** SUCCESS is published only once the instruction's specified architectural effects and telemetry have committed. The write enable, commit telemetry and `inst_done` are set together, but the QR register file samples its registered write enable on the following clock, so publication is no earlier than that commit. Signal names are not evidence of atomicity. A reset coincident with the commit boundary wins: the transaction does not complete.
12. **INV-12 Configuration allowlist.** No unsupported configuration write alters any state other than the permitted transport diagnostics (CFG-4).
13. **INV-13 Reset-scoped identity.** Transaction and rejection identities have meaning only within one reset epoch (§6).
14. **INV-14 No autonomous effect from unsupported requests.** No unsupported request, instruction or configuration, triggers an effect in any protected partition (§9), including autonomous triggers.

## 5. Event ordering, sampling and records

**Two host-visible records (semantic model, not a layout).**

| Record | Updated when | Content (semantic) |
|---|---|---|
| **Transaction record** | An instruction is accepted; then completed | state (NONE / executing / completed); identity; terminal outcome; result-valid; result telemetry (zero or one payload) |
| **Rejection record** | A submission or configuration write is rejected | state (NONE / present); rejection identity; kind; command class if known |

Each record is NONE until its first event after reset. Reset overrides both records. Otherwise the records update **independently**: a completion and a rejection on the same edge update both, and neither suppresses the other.

**Sampling model (proposed).** All events are evaluated at the engine clock edge against the **registered (pre-edge) state**. Same-edge priorities:
1. **Reset** overrides everything: discards the frame, clears both records, invalidates configuration, cancels the transaction.
2. **Frame end.** A recognized frame whose final CRC bit is sampled on an edge at which CS is still asserted is **complete** and is evaluated; CS inactive at or before that sampling edge makes it an **abort**. If a deadman timeout coincides with the sampling of the final CRC bit, the sampled bit **wins** and the frame is evaluated. This is a proposed rule; the existing ordering in the SPI receive logic must be checked against it (AC-7).
3. **Evaluation of a complete frame** (single recorded kind, first applicable): for `0xA5`: malformed header, then unsupported configuration target, then not-ready (INITIALIZING), then configuration-while-busy, then configuration-sequence violation, then (valid) write; for `0xB1`: not-ready (sub-state), then busy, then accept and classify (UNSUPPORTED is an outcome after acceptance).
4. **Acceptance** uses the registered outstanding state before the edge. A request sampled on the edge at which a completion publishes sees the engine outstanding and is rejected as busy.
5. **Same-edge accept and complete** (an instruction that finishes without an observable executing cycle): publish the new identity in the completed state with the committed result. Outstanding ends only after atomic terminal publication and effect commit.
6. **Read snapshot.** The snapshot of both records and the lifecycle/status is taken atomically at the sampling edge of the read command's last bit, from registered values; later updates do not affect the response. A **reset interrupting an SPI read invalidates the entire response**: the host discards it, resynchronizes and retries. A CS drop mid-read ends the read and changes no state (reads are non-destructive).

No accepted request is lost and no rejection identity is skipped.

## 6. Polling, epochs, liveness and recovery

**Reset epochs.** Identities are scoped to one reset epoch. A counter that returns to its initial value after reset cannot distinguish two epochs by value alone, so the contract does not compare identities across a reset boundary. The explicit NONE state of each record is the reset indicator: a record found NONE where a submission or acceptance was expected shows a reset occurred. Hardware need not provide a persistent epoch counter; if one is later added it is an additive indication (D2).

**Host rules (proposed; one host owns the interface).**
1. **Baseline.** After power-up, any reset or any suspected reset, read both records and the lifecycle state. Establish new baselines only after rehydration completes; a rejected rehydration write makes the rejection record non-NONE, so baselines are recorded as explicit (state, identity) pairs rather than assumed zero.
2. **Submit and poll.** Snapshot (transaction state and identity, rejection state and identity). Submit. Poll until either the transaction record shows a new identity and completed, or the rejection record shows a new identity (a new rejection after a submission is attributed to that submission, single host, one submission in flight). For a configuration write, poll the progress/acknowledgement of CFG-7 and the rejection record.
3. **Reset detected mid-submission.** If either record becomes NONE or the lifecycle state falls back, abandon the submission (outcome unknown), then resynchronize and rehydrate before resubmitting.
4. **Bounded loss.** The rejection record keeps the latest kind and an identity counter. The host reads after every submission, so at most one rejection is unobserved per submission. Counters are assumed to see fewer than half their modulus unobserved events; the counter width is chosen at the implementation review subject to that bound and the overrun behavior is documented (D2). Earlier kinds are lost under arbitrary repeated traffic; unsolicited traffic and competing issuers are outside the contract.
5. **Timeout.** No expected record within the documented bound means **UNKNOWN OUTCOME / RECOVERY REQUIRED** (R-4); the host asserts the physical reset if available, then resynchronizes and rehydrates.

**LIVE-1** If clocks run, reset does not intervene and the profile's units terminate, an accepted instruction completes. The completion bound per supported instruction is a profile property to be established; the core-level simulation latencies (QLDI 2 cycles, QSUB 4, ROTC 6, `0x2A` 556) are samples, not bounds. v0 defines no hardware watchdog.

## 7. Outcome semantics and results

Four things are kept distinct: **architectural QR state mutation**, **host-visible result telemetry**, **instruction completion** and **arithmetic refusal**.

| Instruction | Architectural effect | Result telemetry (zero or one) | Publication point |
|---|---|---|---|
| QLDI | QR lane written | commit of the destination lane (one) | after the QR write commits (INV-11) |
| QSUB | QR lane written (two-cycle sequence) | commit of the destination lane (one) | after the write commits |
| ROTC | QR lane written after the rotor completes | commit of the destination lane (one) | after the write commits |
| `0x2A` | **none**: no QR register write | A31 limbs with a lane label (one) | after the telemetry commit |

`0x2A` returns host-visible telemetry; the lane label names the destination associated with the result and is **not** a QR register write. A later QSUB or ROTC cannot consume the `0x2A` result by naming that lane. A future design that writes Padé results to the QR file is a separate architectural decision with its own tests. The simulator must reflect this distinction. The baselines produced exactly one commit per supported instruction (an observation; the payload layout is left to the numerical contract).

- **SUCCESS:** specified effects committed; result-valid true with that one telemetry item.
- **REFUSED:** terminal, no commit. In this profile, arithmetic refusal of `0x2A` (A31 zero divisor): `pade_done && flags_v` is REFUSED, `pade_done && !flags_v` is SUCCESS. This addresses the A31-R2 witness only; it is not a proof that every failure is detected. The one-hot BTU input of this configuration narrows the multiple-result concern; this is an assumption to confirm in the exact image.
- **UNSUPPORTED:** terminal, no effect over the protected partitions, no telemetry.
- **Integrity and other errors.** Transport errors (CRC and related) are rejection events, not outcomes. ECC double errors, RNS errors, quadray-coherence faults, pipeline stalls and other datapath faults require **explicit classification by the owning subsystem** (D7); they are not silently mapped to A31 arithmetic refusal, and no new fault outcome is invented here. Until classified, the contract makes only this guarantee: an accepted transaction affected by such an event MUST NOT be published as SUCCESS with a fresh valid result.
- A refusal may leave physical registers holding old data; that data is never associated with the new transaction or flagged valid.

## 8. Rejection kinds and transport policy

| Case | Policy |
|---|---|
| CRC mismatch on a recognized `0xB1` or `0xA5` frame | Transport rejection, CRC kind; existing `0xAC` CRC sticky preserved. |
| `0xA5` frame with valid CRC but header byte not `0xA5` | Transport rejection, **malformed-header kind**; the legacy CRC sticky is still set, as today. |
| Recognized frame cut off (CS drop, deadman) before completion | Transport rejection, abort kind. |
| CS asserted, command byte incomplete or not B1/A5 | Not classifiable: no rejection event, no effect. |
| `0xA5` target not in the allowlist | Rejection, unsupported-configuration-target kind; nothing written or staged. |
| `0xA5` write during INITIALIZING | Rejection, not-ready kind (sub-state INITIALIZING). |
| `0xA5` write while a transaction is outstanding | Rejection, configuration-while-busy kind. |
| `0xA5` write that violates the manifest sequence | Rejection, configuration-sequence-violation kind; progress cleared (CFG-6). |
| Valid instruction while not execution-READY | Rejection, not-ready kind with sub-state (INITIALIZING, configuration-required, boot FAULT); not replayed. |
| Valid instruction while a transaction is outstanding | Rejection, busy kind; outstanding transaction unaffected. |
| Reset during a frame | Frame discarded; records reset. |

**"Recognized"** means the 8-bit command byte decoded as `0xB1` or `0xA5` while CS stayed asserted, assuming the SPI mode-0 alignment the slave expects; corrupted alignment decodes to whatever byte results.

## 9. Protected state and background activity

State is partitioned by owner. **No unsupported request, instruction or configuration, may trigger an effect in any partition.**

| Partition | Contents (examples, source-grounded) | Gate |
|---|---|---|
| **Instruction-owned** | Quadray register contents and tags; commit telemetry (`qr_commit_*`); result outputs including the ROTC debug word and HEX outputs; rotor, pipeline and SOM start strobes; the instruction-driven Artery output (`0xE0` decode); REGEN counter and chain inputs (`regen_eligible_op`, `chain_op_strobe`) and the chain state | The accepted transaction's latched authorization (INV-5) |
| **Configuration-owned** | Padé coefficient storage and its staged halves; BTU rows; kappa; torus controls (`sel=7`, `torus_emit_enable`, `torus_idx`); any other state addressable through `0xA5` | The allowlist and lifecycle rules of §3 (CFG-4, CFG-6, INV-10, INV-12); not the instruction predicate |
| **Background** | Hydration sweeps, the autonomous stability network, audio and similar clocked blocks, and any autonomous emission | Each must be **explicitly permitted and qualified, or disabled** for the profile; merely excluding its opcode is insufficient. The image manifest enumerates the background blocks that exist. |

The RPLU2 pipeline SOM node weights are fixed by the image: its training port is tied off, so they are not runtime SOM-weight configuration. Any configuration target purporting to change them is outside the allowlist. A rejected incoming word must not gate an in-flight completion, and background activity not attributed to the transaction is outside the "no effect" claim only if it is enumerated and permitted.

## 10. Numerical-semantics contract (mandatory prerequisite)

A **separate numerical-semantics contract** for QLDI, QSUB, ROTC and `0x2A` is mandatory before H0 profile qualification. The author prepares it from source; Codex reviews it independently; it is separate from H0-C1 and non-normative until tested. The current proposed contract is [`H0_NUM1_NUMERICAL_CONTRACT_DRAFT.md`](H0_NUM1_NUMERICAL_CONTRACT_DRAFT.md). Transport and numerical contracts are separately testable: transport tests depend on accepted, completed, outcome and rejection, not on values. A transaction record does not establish numerical correctness or simulator parity.

| Operation | Qualification focus (source facts to resolve) |
|---|---|
| QLDI | Immediate decoding and sign extension, register-lane selection (`qr_lane` wraps an 8-bit index modulo 13), scale and canonical representation (boot hydration uses Q12 `0x1000` per unit; QLDI loads unscaled integers) |
| QSUB | Operand interpretation, arithmetic width (the two 32-bit halves subtract independently), truncation and result state |
| ROTC | Candidate angles `{0, 2, 5}`, identity/permutation mappings, component patterns, tags and committed state; divide-by-three rotations are outside initial H0 |
| `0x2A` | Input interpretation, narrowing of coefficient halves to 18 bits, Padé arithmetic, refusal, telemetry format and lane label; the contents of SET-N and SET-R |

## 11. Relationship to existing SPI commands

| Command | Treatment (proposed) |
|---|---|
| `0xB1` | Command value, framing, big-endian word and CRC unchanged. CRC success is necessary but not sufficient. The strobe becomes an internal request that is accepted or rejected, never silently dropped. |
| `0xA5` | Framing unchanged. Behavior changes for legacy hosts: writes to targets outside the allowlist, writes during INITIALIZING or while a transaction is outstanding, and sequence-violating writes are rejected instead of applied. |
| `0xAC` | Command value, byte layout, documented field meanings and clear/sticky behavior unchanged; its spin-dependent debug meanings are not reused as completion, outcome or configuration state. Use of spare byte-3 bits is open (D4). |
| `0xAE` | Same command, layout and sticky "last commit" meaning; its valid byte MUST NOT be the only freshness evidence. After the refusal fix the latch is updated only by SUCCESS telemetry. |
| New reads | An **additive** mechanism (for example new read-only commands) for the records, lifecycle state and configuration progress is the compatibility-preserving direction; no value or layout is assigned. |

**Compatibility wording.** For existing hosts the command values, framing, field meanings and documented clear/sticky behavior are preserved. Response *values* may change where invalid prior behavior is repaired: an A31 refusal no longer produces a fresh commit (so the first-after-reset refusal no longer leaves `0xAE` valid with undefined data), and `0xA5` writes may now be rejected as listed. Status fields are spin-dependent; no particular spin's value is generalized.

**Real SPI timing is UNVERIFIED (qualification blocker).** H0-V1 results are core-level. A `0xB1` frame is at least 80 SCK bit periods, but the relationship between SCK, `clk_fast` (`A7_CLK_DIV_LOG2`, spin dividers) and the slave's three-sample synchronizer limit is not established. No ratio is assumed and no collision window is claimed reachable on the board. The contract requires hardware rejection (INV-2, INV-3) regardless. No buffering is proposed.

## 12. Verification acceptance criteria (proposed, finite)

Two classes: **core-ingress injection** (clock-level stimulus at the shared ingress/engine interface, exhaustive over the stated offsets) and **SPI integration** (serialized frames at explicitly identified operating points). Held-valid means *one* request held high for several cycles: exactly one acceptance or one rejection. The H0-V1 and A31-R2 probes are starting fixtures.

| ID | Criterion |
|---|---|
| AC-1 | Each supported instruction alone (QLDI, QSUB, each angle of the candidate ROTC set `{0, 2, 5}`, `0x2A` under SET-N): one acceptance, one record with SUCCESS, result-valid, and the expected state and telemetry. |
| AC-2 | Opcode classes: all 256 opcode values with a canonical operand pattern; per operand field the boundary values {all zero, all ones, unused/reserved bits set}, lane-index classes {0, 12, 13, 127, 255}, QLDI immediate sign classes, and ROTC angle classes {{0, 2, 5}; every other angle 0-63, with unused-bit patterns}. Each unsupported case: one UNSUPPORTED record, no telemetry, no change over the instruction-owned, configuration-owned and enumerated background partitions. |
| AC-3 | Core-ingress: a second instruction at every cycle offset within each supported instruction's window (QLDI, QSUB, ROTC; `0x2A` over its full latency plus margin) and held-valid: rejected visibly as busy; the outstanding transaction completes with the correct result and exactly one record. A rejected unsupported word during an authorized operation does not gate it (INV-5). |
| AC-3b | Simultaneous completion and rejection update both records; no rejection identity skipped; acceptance decided against pre-edge state; same-edge accept-and-complete publishes the new identity completed with the committed result. |
| AC-3c | `0xA5` write at every offset during an outstanding transaction: rejected visibly, nothing written, the operation sees one configuration. |
| AC-4 | A31 refusal with real configurations: SET-N success → return to CONFIG_REQUIRED → load SET-R → refusal → reload SET-N → recovery success; and the refusal first after reset (reset → SET-R → refusal). Refusal: REFUSED, no result-valid, no telemetry, no stale or `x` value, no late publication; simultaneous error/done behaves as classified. Fault injection for RNS/ECC events is conditional on the D7 classification. |
| AC-5 | Consecutive identical instructions give distinguishable transaction identities; consecutive identical rejections give distinguishable rejection identities; counter wrap and a soak across the modulus behave as specified; a reset between snapshot and poll is detected by the NONE state, with no cross-epoch comparison. |
| AC-6 | Not-ready: rejected visibly with its sub-state (INITIALIZING, configuration-required, boot FAULT), not replayed. |
| AC-7 | Bad CRC; malformed `0xA5` header with valid CRC (legacy sticky preserved); recognized-B1 and recognized-A5 aborts; unclassifiable fragment; CS drop at, before and after the final-bit sampling edge; deadman coincident with the final bit; reset at each frame phase: classification and same-edge priority per §5; no acceptance and no effect on abort. |
| AC-8 | Reads return one coherent snapshot of both records and lifecycle state; reads during each update and simultaneous read/completion, read/rejection, acceptance/rejection and reset follow §5; **interrupted reads**: reset or CS drop mid-read invalidates or ends the response and changes no state. |
| AC-9 | Reset during execution, during a staged coefficient pair, during a frame, and while idle; host timeout followed by reset: no record claims completion, no late event, both records NONE, configuration invalid until rehydrated, resynchronization works. |
| AC-10 | Compatibility: framing and field semantics of `0xB1`, `0xA5`, `0xAC`, `0xAE` unchanged; unaffected successful transactions give byte-identical legacy responses; legacy `0xAE` retention after a refusal matches §11; the legacy behaviors that change (§11) are the only differences. |
| AC-11 | A finite, named set of SPI/clock operating points (SCK, divider, phase offsets, CS setup/hold) fixed at qualification, with synchronizer margin measured; the serialized cases of AC-1 to AC-10 run at each. |
| AC-12 | Synthesis and timing of the exact image, then the supported, physically reachable suite on the board with preserved logs, build manifest and a hardware-evidence entry. Simulation, timing and physical results are reported as separate evidence levels. |
| AC-13 | Configuration lifecycle and allowlist: reset → INITIALIZING (writes rejected) → CONFIG_REQUIRED (writes accepted) → valid → READY; instructions rejected before valid; every non-allowlisted target, including `sel=7` torus control and any purported SOM weight targets, rejected with no state change; SET-N and SET-R each accepted only when written in full canonical order; duplicate, omitted, reordered, unexpected-value and stale-half writes rejected and progress cleared; per-write acknowledgement observed with its bounded wait; a covered write after valid returns to CONFIG_REQUIRED; switching sets requires the full sequence. |
| AC-14 | Commit before publish: a QLDI/QSUB/ROTC record is never published before the QR write has committed; reset at the commit boundary leaves no completed record; a following instruction sees the committed state. |
| AC-15 | `0x2A` telemetry: exactly one terminal record; telemetry only, no QR register-file write; result associated with its record across consecutive operations; no late results; the one-hot BTU assumption confirmed in the exact image. |
| AC-16 | Elaboration check that disabled REGEN removes its counter **and** the chain instance (or both are explicitly gated), and that the image enables only the listed blocks and permitted background activity. |
| AC-17 | Board-level reset: the documented physical reset mechanism of the actual Wukong setup asserts reset reliably and repeatedly (power-up and power-cycle behavior included), and the host can use it for timeout recovery. |

## 13. Decisions

**Resolved by owner decision for r4:** reset provider (physical), configuration allowlist, SET-N/SET-R, ordered hardware-checked comparison, INITIALIZING rule, reset-scoped identity, integrity-error separation, ROTC as candidates, numerical contract ownership, configuration after reset (mandatory host-driven rehydration), `0x2A` telemetry-only.

**Remaining architectural decisions:**
- **D1** Record owner and wiring: the Artix-7 top is the natural owner; each included engine needs explicit accepted, terminal, outcome and result-event signals.
- **D2** Identity and generation widths, wrap and overrun behavior, and whether an additive persistent epoch indication is ever needed.
- **D3** Remaining edge details beyond §5 for each included instruction.
- **D4** Spare `0xAC` bits versus additive read commands; tying `0xAE` content to the completion.
- **D5** Location of the shared classifier and its latching, kept equal to the build's enable parameters.
- **D6** Qualify candidate ROTC angles `{0, 2, 5}` on the proposed image; no broader angle set is approved.
- **D7** Subsystem-specific classification of RNS, ECC, quadray-coherence and stall events.
- **D8** Rejection record: latest-only plus generation versus per-kind sticky/overrun indicators.
- **D9** The legacy `inst_done` port (internal completion input versus removal).
- **D10** Build configuration (CUSTOM versus new spin, REGEN disable at the top, `fpga_chain` handling, listed peripherals, timing closure).
- **D11** Completion bounds per instruction and the derived host timeout.
- **D12** SPI timing relationship and the operating-point set.
- **D13a** How the manifest is selected in the canonical sequence. **D13b** Representation of per-write acknowledgement and the lifecycle state.
- **D14** The exact contents and recorded identities of SET-N and SET-R, and the full allowlist of `(selector, material, address, value)` entries.
- **D15** Encoding and visibility of lifecycle states.
- **D16** The physical reset mechanism on the actual board (button, GPIO or other) and its documentation.

## 14. Out of scope

New instructions or mathematical changes; a queue or sequencer; a soft-reset command; a bootloader, dynamic configuration manager or cryptographic verifier; a unified FLAGS register (see SNAP-1); A31 arithmetic redesign (the repair is validity propagation); choice of SPI encodings, counter widths or buffering; SPU-4; DELTA, HEX, REGEN, IROTC, SOM, Surd, SU3, Lucas and Neuro semantics; the numerical-semantics contract itself.
