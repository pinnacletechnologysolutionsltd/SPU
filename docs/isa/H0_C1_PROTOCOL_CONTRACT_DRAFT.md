# H0-C1 — Minimum host-driven execution protocol: contract draft (revision 2)

**Status:** NON-NORMATIVE DRAFT for independent review. Nothing here is implemented, qualified, ratified or an encoding. Normative ratification and RTL implementation **HOLD**.
**Revision:** r2. r1 was committed as `ff98404134ae63bc481e9ea9d6dd4d3ad1398f8e`; this revision supersedes it in place (r1 remains in git history).
**Baseline identity for this revision:** `dev/next` at `ff98404134ae63bc481e9ea9d6dd4d3ad1398f8e` (clean before editing). Existing VM, assembler and RTL sources are unchanged from public RC2 `b063280`.
**Language:** MUST/SHALL mark requirements of this *proposed* contract, not properties of the current design. No instruction-set or mathematical change; no queue; no autonomous program counter; no unified FLAGS register; no counter width, SPI command value or bit position is assigned.

## 0. What changed from r1

An independent review of r1 (`/tmp/H0-C1-independent-review-ff98404.md`, stored outside the repository; reviewed tree `dev/next` `ff98404`; produced by the Codex reviewer at the owner's direction; no other review identifier exists) raised nine findings, C1-1 to C1-9. Their disposition is in §13. The owner approved freezing a small initial profile (§2) instead of a universal protocol, and set: one completion record plus separate, freshness-qualified rejection events; safety separated from conditional liveness; configuration writes accepted only while idle; zero or one `0xAE` payload per successful instruction. I verified the review's main source claims before accepting them (DELTA emits no commit telemetry; REGEN gives two commits; `regen_eligible_op` includes `0x14`/`0x18`; the bad-angle ROTC strobes are computed before the angle fault branch; SU3 is a session; Padé coefficient writes are not gated by the evaluator state).

## 1. Evidence base

| Source | What it establishes (as built) |
|---|---|
| [`ISA_V02_STATE1_FINDINGS.md`](ISA_V02_STATE1_FINDINGS.md) | The core acknowledges unsupported opcodes with `inst_done` and no effect; no success/refusal signal. |
| [`ISA_V02_H0TRANSPORT1_FINDINGS.md`](ISA_V02_H0TRANSPORT1_FINDINGS.md) | `0xB1` yields a one-cycle strobe with no queue or acknowledgement; `inst_done` is not host-visible; silent drops; `0xAE` valid is sticky with no freshness. |
| [`ISA_V02_H0V1_FINDINGS.md`](ISA_V02_H0V1_FINDINGS.md) | Core-level simulation: overlapping strobes can swallow an instruction or lose an in-flight ROTC result; 40 opcodes acknowledged without effect on QR state (QR-only check, see §4 INV-5); boot-not-ready strobes lost; identical repeated results indistinguishable; the Padé sidecar rejects a busy request correctly. In the baselines QLDI, QSUB, ROTC and `0x2A` each produced exactly one commit. |
| [`ISA_V02_A31R2_FINDINGS.md`](ISA_V02_A31R2_FINDINGS.md) | Simulation: after an A31 inversion refusal the ordinary pipeline and core bridge publish the previous result (or `x`) with valid indications; the Padé sidecar suppresses the commit. One zero-divisor witness. |

## 2. Initial profile (provisional name): SPU-H0-RPLU2-v0.2

These are **proposed profile requirements**, not a claim that the current RTL enforces them or that any image has been built or qualified.

| Item | Decision |
|---|---|
| Device | Artix-7 XC7A100T |
| Execution | Host-driven, one outstanding instruction across the whole engine |
| Core configuration | `spu13_core` with the RPLU2 pipeline enabled; `ENABLE_MATH` enabled (required by ROTC) |
| Disabled | REGEN, legacy core SOM (`ENABLE_CORE_SOM`), IROTC, Surd extension, RPLU2 extension bundle (JSCR/NSA) |
| Excluded sidecars | Lucas, SU3, Neuro, live-evaluator and Padé sidecar spins (coreless spins also tie `boot_ready` low) |
| Not present | Scalar registers, PC, call stack |
| **Supported** | QLDI (`0x1D`), QSUB (`0x1B`), ROTC (`0x1C`) restricted to an explicitly qualified angle set, RPLU2 start (`0x2A`, which includes the pipeline's internal SOM, BTU and Padé stages) |
| **Unsupported** | Every other opcode value, and ROTC with an angle outside the qualified set |
| Excluded semantics | DELTA, HEX, REGEN, IROTC, SOM, Surd, SU3, Lucas, Neuro (their executable semantics are not defined by this contract; research evidence is unaffected) |

**Current-implementation gaps against this profile (source facts):** (a) no existing named Artix-7 spin has this configuration: the `RPLU2` spin sets `ENABLE_MATH` to 0 (so ROTC would hang) and `MULTIMEDIA`/`FULL` carry GPU/I2S/SOM; the profile needs a `CUSTOM` configuration or a new spin (not built here); (b) `spu_a7_top.v` does not pass `ENABLE_REGEN`, which defaults to 1, so disabling REGEN needs a top-level change in the implementation phase; (c) the qualified ROTC angle set is undecided: the RTL gate admits 0-35 (`ROTC_MAX_VERIFIED_ANGLE`) and the evidence ledger records silicon for angles 0-5: a Tang 25K probe (§3.2g) and Artix-7 ROBOTICS coverage that §3.2g refers to (the Artix-7 entry was not re-read here); (d) whether the configuration closes timing is unknown. **Choice made here:** a ROTC angle outside the qualified set is UNSUPPORTED (classified before any side effect), which also removes the existing bad-angle fault path from the profile; REFUSED is reserved for arithmetic refusal (§6).

## 3. Vocabulary and event model

> **Safety:** no accepted instruction produces more than one terminal outcome, and no refused or unsupported instruction publishes a fresh valid result.
> **Liveness (conditional):** an accepted instruction eventually completes, provided clocks continue, reset does not intervene and the profile's execution assumptions hold (§5).

| Term | Definition (proposed) |
|---|---|
| **Submitted** | A frame carrying an instruction word reached the ingress. |
| **Transport-rejected** | Not delivered to the engine (CRC failure, aborted frame). |
| **Rejected at acceptance** | Delivered but not taken: engine not READY, a transaction outstanding, or (for configuration) not idle. |
| **Accepted** | Execution ownership transferred to the engine. CRC success is necessary, not sufficient. |
| **Completed** | The accepted transaction reached its terminal outcome and its record is published. |
| **Succeeded / Refused / Unsupported** | Terminal outcomes SUCCESS, REFUSED (execution ended without publishing an invalid result, e.g. A31 zero-divisor), UNSUPPORTED (opcode or operand outside the supported subset; no effect). |
| **Result-valid** | A fresh result accompanies the transaction; independent of completion. |

`inst_done` MUST NOT be read as success. The existing pulse MAY remain as an internal completion input to the record, after opcode-specific success or fault and result timing are validated (it is asserted today for unsupported opcodes).

**Two kinds of host-visible event (semantic model, not a layout):**

| Event kind | Produced when | Content (semantic) | Freshness |
|---|---|---|---|
| **Transaction record** | An instruction is accepted, then completed | transaction identity; state (executing / completed); terminal outcome (SUCCESS / REFUSED / UNSUPPORTED); result-valid; result data (zero or one payload) | identity changes on every acceptance |
| **Rejection record** | A submission or configuration write is rejected | rejection kind (transport CRC, transport abort, not-ready, busy, configuration-while-busy); command class if known (instruction or configuration) | its own event identity changes on every rejection |

Rejections never alter the transaction record; acceptance and completion never alter the rejection record. Both records are in a defined "none yet" state after reset.

## 4. Safety invariants (proposed)

1. **INV-1 At most one terminal outcome** per accepted instruction (no outcome is ever published twice, and none for a cancelled transaction).
2. **INV-2 Single outstanding, enforced by hardware.** Outstanding runs from acceptance until the record is published (not merely until a pulse), across the core and everything behind the ingress. A second instruction is rejected visibly, independent of host behavior.
3. **INV-3 Rejected traffic is inert.** A rejected instruction or configuration write never alters, delays or discards an in-flight operation's step or result, including when the rejection coincides with a completion (H0-V1: swallow, ROTC loss).
4. **INV-4 No fresh-valid on refusal.** REFUSED and UNSUPPORTED transactions raise no result-valid, commit or commit-telemetry update, and never present a previous result or an undefined value as fresh, including after reset (A31-R2). No late publication occurs after cancellation (§5).
5. **INV-5 Classification precedes every side effect.** One shared supported-opcode predicate (including the ROTC qualified angle set), evaluated before any decode block acts, gates *all* effects: Quadray register writes and tags, commit telemetry, any other result output, configuration registers, rotor and pipeline start strobes, the Artery output port, REGEN counter and chain state (absent in this profile, to be confirmed in the image), and any autonomous trigger. "No effect" is therefore defined over the protected-state set, not over QR registers alone (the H0-V1 unsupported probe checks QR state only).
6. **INV-6 Rejections are visible, distinct and fresh** (§7).
7. **INV-7 Distinct consecutive transactions:** records of N and N+1 are distinguishable even when results are identical.
8. **INV-8 Record stability and coherence:** a published record is stable until the next acceptance or reset; its fields are mutually coherent.
9. **INV-9 Transport status is separate from arithmetic status:** CRC, abort and rejection kinds share no meaning with SUCCESS, REFUSED or UNSUPPORTED.
10. **INV-10 Configuration is immutable while a transaction is outstanding.** Configuration writes (including Padé coefficient writes through `0xA5`) are accepted only while the engine is idle; otherwise they are rejected with a configuration-while-busy rejection record and write nothing.

## 5. Conditional liveness, timeout and reset

- **LIVE-1.** If clocks run, reset does not intervene and the profile's units terminate, an accepted instruction completes. The completion bound for each supported instruction is a profile property to be established; the core-level simulation latencies (QLDI 2 cycles, QSUB 4, ROTC 6, `0x2A` 556) are samples, not bounds.
- **Reset** cancels the outstanding transaction. After reset both records are in the "none yet" state and boot gating applies; a transaction in flight at reset is not completed, no record claims it, and no late event from the cancelled engine may publish (the engine is reset, not merely abandoned).
- **Host timeout** is not an architectural outcome and MUST NOT be reported as REFUSED. A host that times out treats the transaction as **outcome unknown** and resets, then reads the "none yet" state before any further submission (resynchronization). v0 defines no hardware watchdog; a future watchdog would require cancellation or isolation guaranteeing no late publication and no second outcome.
- **Fatal conditions.** A unit that never completes (for example ROTC with math disabled, which the profile excludes by configuration) is covered by the timeout-and-reset rule.

## 6. Outcome semantics

- **SUCCESS:** specified effects committed. In the baselines each of QLDI, QSUB, ROTC and `0x2A` produced exactly one commit; the profile requires result-valid true for these with that one payload (the destination lane, or the Padé A31 limbs) as the zero-or-one `0xAE` payload. State effects without telemetry (as DELTA) are excluded from the profile.
- **REFUSED:** terminal, no commit. In this profile, arithmetic refusal of `0x2A` (A31 zero divisor): the consumer classifies `pade_done && flags_v` as REFUSED and `pade_done && !flags_v` as SUCCESS. This addresses the A31-R2 witness only; it is not a general proof of success. Other error events (`rns_error`, quadray-coherence fault, pipeline stall, busy) are not assumed to be refusals: each must be classified per profile as terminal, diagnostic or transport-level, and associated with the owning transaction (open decision D7).
- **UNSUPPORTED:** terminal, no effect over the protected-state set (INV-5), no commit. Includes feature-disabled opcodes and ROTC angles outside the qualified set.
- Completion is independent of result-valid. A refusal may leave physical registers holding old data; that data is never associated with the new transaction or flagged valid.

## 7. Rejection, abort and transport policy

| Case | Policy |
|---|---|
| CRC mismatch on a recognized `0xB1` or `0xA5` frame | Transport rejection (CRC kind); frame discarded; existing `0xAC` CRC sticky behavior preserved. |
| `0xB1`/`0xA5` recognized (the 8-bit command decoded) but CS dropped or deadman fired before the frame completed | Transport rejection (abort kind). Command class is known. |
| CS asserted, command byte incomplete or not a B1/A5 command | Not classifiable as an instruction or configuration frame: no rejection event; no effect on any record. |
| Valid frame while not READY | Rejection (not-ready kind); boot FAULT distinguishable from HYDRATING. Not replayed. |
| Valid instruction while a transaction is outstanding | Rejection (busy kind); outstanding transaction unaffected. |
| Configuration write while not idle | Rejection (configuration-while-busy kind); no write. |
| Reset during a frame | Frame discarded; records reset. |

**Rejection freshness.** Each rejection advances its own event identity and records its kind. The record holds the most recent rejection and the identity, so two consecutive identical rejections are distinguishable and the host can tell that at least one rejection occurred since its last read. Under arbitrary repeated traffic earlier reasons are overwritten (bounded loss: only the latest reason is retained, the identity count is preserved modulo its width). The alternative of requiring the host to read after every submission is the stated observation discipline; whether to also keep a per-kind sticky indicator is open (D8). Simultaneous-update precedence (proposed): reset, then completion publication, then acceptance, then rejection; a read snapshots one coherent state (§8).

## 8. Host-visible record requirements (no encoding)

For the transaction record and the rejection record the host MUST be able to read, coherently and non-destructively:

- Transaction record: identity; state; terminal outcome; result-valid; when result-valid, the payload associated with this transaction (carried by the record, or guaranteed to be the `0xAE` content for this completion).
- Rejection record: identity; kind; command class.
- Engine status: ready / busy / boot state.

**Lifetime and stability.** The transaction record persists from publication until the next acceptance or reset. Reading never clears either record. Fields are captured atomically at publication, and a read returns one coherent snapshot (the old or the new record, never a mixture). A transaction that completes in the same cycle it is accepted still yields a record with a new identity and a completed state (the "executing" state may never be observed). **Identity.** Acceptance identity changes on every acceptance and has a defined reset state. A one-bit alternating tag is sufficient only for a single host that consumes every record before the next submission and resynchronizes after reset; it is not robust against unobserved transactions or reset aliasing, so a wider counter with a defined wrap is preferred (width is open, D2). **Polling discipline (proposed):** submit; read until the record shows the new identity as completed (documented timeout); then submit the next.

## 9. Relationship to existing SPI commands

| Command | Treatment (proposed) |
|---|---|
| `0xB1` | Command value, framing, big-endian word and CRC unchanged. CRC success is necessary but not sufficient for acceptance. The strobe becomes an internal request that is accepted or rejected, never silently dropped. |
| `0xA5` | Framing unchanged. Writes are accepted only while idle (INV-10); a write during an outstanding transaction is rejected visibly. This changes behavior for a legacy host that writes coefficients during an operation (the prior behavior could corrupt that operation). |
| `0xAC` | Command value, byte layout, documented field meanings and clear/sticky behavior unchanged. Its spin-dependent debug meanings (H0-TRANSPORT-1) are not reused as completion or outcome. Whether spare zero bits of byte 3 are used is open (D4). |
| `0xAE` | Same command, layout and sticky "last commit" meaning. Its valid byte MUST NOT be the only freshness evidence. After the refusal fix the latch is updated only by SUCCESS commits. |
| Record read | An **additive** mechanism (for example a new read-only command) is the compatibility-preserving direction; no value or layout is assigned here. |

**Compatibility wording.** For existing hosts the command values, framing, field meanings and documented clear/sticky behavior are preserved. Response *values* may change where invalid prior behavior is repaired: an A31 refusal no longer produces a fresh commit (so, for example, the first-after-reset refusal no longer leaves `0xAE` valid with undefined data), and `0xA5` writes during an outstanding transaction are now rejected. Status fields are spin-dependent; no value of a particular spin is generalized.

## 10. Real SPI timing: qualification blocker (UNVERIFIED)

H0-V1 results are core-level results under supplied one-cycle strobes. A `0xB1` frame is at least 80 SCK bit periods, but the relationship between SCK, `clk_fast` (`A7_CLK_DIV_LOG2`, spin dividers) and the SPI slave's three-sample synchronizer limit is not established. This draft assumes no ratio and claims no collision window is reachable on the board. The contract requires hardware rejection (INV-2, INV-3) regardless of reachability. The independent reviews' sampling-margin question remains untested and is a blocker for physical qualification. No buffering is proposed.

## 11. Verification acceptance criteria (proposed, finite)

Two classes: **core-ingress injection** (clock-level stimulus at the shared ingress/engine interface, exhaustive over the stated offsets) and **SPI integration** (serialized frames at explicitly identified operating points). Gap 1 is held-valid protocol behavior, not two independent packets. The H0-V1 and A31-R2 probes are starting fixtures; the unsupported-opcode QR hash is a starting sample, not state proof.

| ID | Criterion |
|---|---|
| AC-1 | Each supported instruction alone (QLDI, QSUB, each qualified ROTC angle, `0x2A`): one acceptance, one record with SUCCESS, result-valid and the expected state and payload. |
| AC-2 | All 256 opcode values, plus every ROTC angle 0-63 and operand-field variants: each unsupported case produces one UNSUPPORTED record with no commit and no change over the protected-state set (QR file and tags, commit and result outputs, configuration and coefficient registers, start strobes, the Artery port, REGEN state if present, autonomous triggers). |
| AC-3 | Core-ingress: a second instruction at every cycle offset within each supported instruction's window (QLDI, QSUB, ROTC; `0x2A` over its full latency plus margin), and held-valid: rejected visibly as busy, outstanding transaction completes with the correct result and exactly one record; rejection coinciding with completion leaves the record intact. |
| AC-3b | Configuration write at every offset during an outstanding transaction: rejected visibly, nothing written, the operation sees one configuration; a write while idle succeeds and legacy hosts' idle writes are unchanged. |
| AC-4 | A31 refusal after a success and first after reset, through the core path with the pipeline in this profile: REFUSED, no result-valid, no commit, no stale or `x` value; a following valid transaction succeeds; simultaneous error/done and any other classified error events behave as classified (D7); no late publication. |
| AC-5 | Consecutive identical instructions give distinguishable transaction identities; consecutive identical rejections give distinguishable rejection identities; identity rollover and the reset state behave as specified. |
| AC-6 | Boot-not-ready: rejected visibly, not replayed; boot FAULT distinguishable from HYDRATING. |
| AC-7 | Bad CRC, recognized-B1 abort (CS drop, deadman), unclassifiable fragment, reset at each frame phase: classification per §7; no acceptance and no effect; existing `0xAC` CRC sticky unchanged. |
| AC-8 | Record stability: repeated reads (including across CS toggles) return the same coherent record; reads during each update, and simultaneous read/completion, rejection/completion, acceptance/rejection and reset, follow the stated precedence; payload coherent with the record. |
| AC-9 | Reset during execution and host timeout followed by reset: no record claims completion, no late event, defined post-reset state, resynchronization works. |
| AC-10 | Compatibility: command framing and field semantics for `0xB1`, `0xA5`, `0xAC`, `0xAE` unchanged; unaffected successful transactions give byte-identical legacy responses; legacy `0xAE` retention after a refusal matches the corrected behavior of §9; `0xA5` idle writes unchanged. |
| AC-11 | A finite, named set of SPI/clock operating points (SCK, divider, phase offsets, CS setup/hold) is fixed at qualification, with synchronizer margin measured; AC-1 to AC-10 serialized cases run at each. Not "each combination". |
| AC-12 | Synthesis and timing of the exact image, then the supported, physically reachable suite on the board with preserved logs, build manifest and a hardware-evidence entry. Simulation, timing and physical results are reported as separate evidence levels. |

## 12. Remaining architectural decisions (owner / independent review)

- **D1** Record owner and wiring: the Artix-7 top is the natural owner; each included engine needs explicit accepted, terminal, outcome and result-event signals (a small controller/adapter, not zero new logic).
- **D2** Identity width, wrap and reset state; whether to keep a 1-bit tag at all.
- **D3** Same-edge acceptance/completion rule (fast instructions) and the exact point at which "outstanding" ends.
- **D4** Spare `0xAC` bits versus an additive record command; and how `0xAE` content is tied to the completion (freeze until consumed, or carry the payload in the record).
- **D5** Location of the shared classifier and how it is kept equal to the build's enable parameters.
- **D6** The qualified ROTC angle set (candidates: the silicon-recorded 0-5, see §2, versus the RTL-gated 0-35).
- **D7** Classification of non-inverter error events in the pipeline (`rns_error`, quadray incoherence, stall) as terminal, diagnostic or transport-level.
- **D8** Rejection record: per-kind sticky indicators versus latest-only with counter; recognizability boundary for aborts.
- **D9** Fate of the legacy `inst_done` port (internal completion input versus removal).
- **D10** Build configuration of the profile (CUSTOM versus a new spin, REGEN disable at the top, timing closure).
- **D11** Completion bounds per supported instruction, and the host timeout derived from them.
- **D12** SPI timing relationship and the operating-point set (§10).

## 13. Disposition of the independent review (C1-1 to C1-9)

| Finding | Resolution in r2 |
|---|---|
| C1-1 rejection freshness, abort visibility | Separate rejection record with its own identity (§3, §7, §8); abort required when the command is recognized, none for unclassifiable fragments; bounded-loss rule; contradiction with the r1 optional abort statement removed. |
| C1-2 SU3 is a session | SU3 and Lucas excluded; busy defined for single-instruction units only (§2). |
| C1-3 supported subset and result cardinality | Profile frozen; result model zero or one `0xAE` payload; DELTA, HEX, REGEN excluded (§2, §6). |
| C1-4 "no effect" broader than QR state | Protected-state set and classifier-first INV-5; AC-2 broadened; ROTC out-of-set angles are UNSUPPORTED before any side effect. |
| C1-5 progress, reset, timeouts | Safety (at most one outcome) separated from conditional liveness; timeout is outcome-unknown plus reset; no watchdog in v0 (§5). |
| C1-6 `0xA5` mid-operation | Configuration accepted only while idle; rejection kind and compatibility note (INV-10, §9). |
| C1-7 `flags_v` is not a general classifier | Scoped to the witness; other error events classified per profile (§6, D7). |
| C1-8 compatibility wording | Preserved framing, meanings and clear/sticky behavior; values may change where repaired (§9). |
| C1-9 acceptance criteria | Split into core-ingress and SPI integration; finite operating-point set; gap 1 treated as held-valid (§11). |

The review's answers to the earlier open questions are adopted where consistent: one current record with a state field suffices under strict one-outstanding polling; the top is the natural owner; a wider identity counter is preferred; the record and payload are captured atomically; one shared classifier; timeout-plus-reset is the minimal recovery; `inst_done` is retained only as an internal completion input; Lucas, SU3 and the live-evaluator sidecar are excluded from the initial image.

## 14. Out of scope

New instructions or mathematical changes; a queue or sequencer; a unified FLAGS register (see SNAP-1); A31 arithmetic redesign (the repair is validity propagation, not arithmetic); choice of SPI encodings, counter widths or buffering; SPU-4; DELTA, HEX, REGEN, IROTC, SOM, Surd, SU3, Lucas and Neuro semantics.
