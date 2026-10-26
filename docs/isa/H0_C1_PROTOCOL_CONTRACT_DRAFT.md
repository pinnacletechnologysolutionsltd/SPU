# H0-C1 — Minimum host-driven execution protocol: contract draft (revision 3)

**Status:** NON-NORMATIVE DRAFT for independent review. Nothing here is implemented, qualified, ratified or an encoding. Normative ratification and production RTL **HOLD**.
**Revision:** r3. r1 was committed as `ff98404134ae63bc481e9ea9d6dd4d3ad1398f8e`, r2 as `96c75a6c8b447a4c7168ef5b75f4109d75d8e1db`; this revision supersedes them in place (both remain in git history).
**Baseline identity for this revision:** `dev/next` at `96c75a6c8b447a4c7168ef5b75f4109d75d8e1db` (clean before editing). Existing VM, assembler and RTL sources are unchanged from public RC2 `b063280`.
**Language:** MUST/SHALL mark requirements of this *proposed* contract, not properties of the current design. No instruction-set or mathematical change; no queue; no autonomous program counter; no unified FLAGS register; no counter width, SPI command value or bit position is assigned.

## 0. What changed

Independent reviews of r1 (`/tmp/H0-C1-independent-review-ff98404.md`) and r2 (`/tmp/H0-C1-r2-independent-review-96c75a6.md`) are stored outside the repository; both were produced by the Codex reviewer at the owner's direction and no other review identifier exists. I verified the main source claims of the r2 review before accepting them (coefficient storage has no reset branch; a CRC-valid `0xA5` packet with a wrong header byte sets the CRC sticky; `fpga_chain u_chain` is instantiated outside the `ENABLE_REGEN` generate, `spu13_core.v:1107` versus `:1134`; the `0x2A` result is telemetry and asserts no `qrf_wr_en`).

Owner decisions approved for r3: (1) mandatory host-driven configuration rehydration before the engine is execution-READY, after every reset; (2) a separate numerical-semantics contract for QLDI, QSUB, ROTC and `0x2A` is a mandatory prerequisite for H0 profile qualification, with transport review continuing independently; (3) `0x2A` is a host-visible result-producing operation with a lane label that does **not** write the Quadray register file in H0.

| r2-review finding | Where resolved in r3 |
|---|---|
| R2-1 simultaneous completion and rejection | §5 |
| R2-2 classifier lifetime | §4 (INV-5), §9 |
| R2-3 polling both identities | §6 |
| R2-4 `0x2A` is telemetry | §7 |
| R2-5 numerical semantics | §10 |
| R2-6 reset versus configuration | §3 |
| R2-7 malformed `0xA5` header | §8 |
| R2-8 ROTC candidate set | §2, §10 |
| R2-9 commit timing, verification scope | §4 (INV-11), §11 |

## 1. Evidence base

| Source | What it establishes (as built) |
|---|---|
| [`ISA_V02_STATE1_FINDINGS.md`](ISA_V02_STATE1_FINDINGS.md) | The core acknowledges unsupported opcodes with `inst_done` and no effect; no success/refusal signal; different QR hydration and `QLDI` scales. |
| [`ISA_V02_H0TRANSPORT1_FINDINGS.md`](ISA_V02_H0TRANSPORT1_FINDINGS.md) | `0xB1` yields a one-cycle strobe with no queue or acknowledgement; `inst_done` not host-visible; silent drops; `0xAE` valid is sticky with no freshness. |
| [`ISA_V02_H0V1_FINDINGS.md`](ISA_V02_H0V1_FINDINGS.md) | Core-level simulation: overlapping strobes can swallow an instruction or lose an in-flight ROTC result; 40 opcodes acknowledged without effect on QR state (a QR-only check); boot-not-ready strobes lost; identical repeated results indistinguishable; the Padé sidecar rejects a busy request correctly. |
| [`ISA_V02_A31R2_FINDINGS.md`](ISA_V02_A31R2_FINDINGS.md) | Simulation: after an A31 inversion refusal the ordinary pipeline and core bridge publish the previous result (or `x`) with valid indications; one zero-divisor witness. |

## 2. Initial profile (provisional name): SPU-H0-RPLU2-v0.2

Proposed profile requirements, not a claim that the current RTL enforces them or that any image has been built or qualified.

| Item | Decision |
|---|---|
| Device | Artix-7 XC7A100T |
| Execution | Host-driven, one outstanding instruction across the whole engine |
| Core configuration | `spu13_core` with the RPLU2 pipeline enabled; `ENABLE_MATH` enabled (ROTC requires it) |
| Disabled | REGEN, legacy core SOM (`ENABLE_CORE_SOM`), IROTC, Surd extension, RPLU2 extension bundle (JSCR/NSA) |
| Other peripherals | Every enable not listed in this table is off in the profile image (GPU, I2S, torus, lattice, SDRAM, gatekeeper and so on); the image's full parameter set is recorded in its build manifest |
| Excluded sidecars | Lucas, SU3, Neuro, live-evaluator and Padé-sidecar spins (coreless spins also tie `boot_ready` low) |
| Not present | Scalar registers, PC, call stack |
| **Supported** | QLDI (`0x1D`), QSUB (`0x1B`), ROTC (`0x1C`) with an angle in the profile's angle set, RPLU2 start (`0x2A`, including the pipeline's internal SOM, BTU and Padé stages) |
| **Unsupported** | Every other opcode value, and ROTC with an angle outside the set |
| Excluded semantics | DELTA, HEX, REGEN, IROTC, SOM, Surd, SU3, Lucas, Neuro |

**Current-implementation gaps against the profile (source facts).** (a) No existing named Artix-7 spin has this configuration: the `RPLU2` spin sets `ENABLE_MATH` to 0 (ROTC would hang), `MULTIMEDIA` and `FULL` carry GPU/I2S (and SOM in `FULL`); the profile needs a `CUSTOM` configuration or a new spin. (b) `spu_a7_top.v` does not pass `ENABLE_REGEN`, which defaults to 1: disabling it needs a top-level change. (c) `fpga_chain u_chain` is instantiated outside the `ENABLE_REGEN` generate and is driven by a strobe computed from QLDI, QSUB and ROTC acceptance (`chain_op_strobe`): "chain state absent" must be verified by elaboration or the instance explicitly gated; in either case its inputs are gated by the transaction authorization of INV-5. (d) Whether the configuration closes timing is unknown.

**ROTC angle set.** Angles **0-5 are a conservative candidate set, not a qualified one.** The ledger records ROTC 0-5 silicon in two places with different scopes: a Wukong Artix-7 ROBOTICS main-core smoke (§3.0, corrected angles 0-5) and a dedicated Tang 25K probe (§3.2g). Neither qualifies the new combined image, its operand boundaries or this protocol; the RTL gate `ROTC_MAX_VERIFIED_ANGLE = 35` is a decode bound, not evidence. Angles outside the final set are UNSUPPORTED, classified before any side effect (a profile policy, not a globally ratified ISA rule; it differs from the current core's >35 bad-angle diagnostic path). Qualification of the set is in §10.

## 3. Configuration lifecycle and readiness

Concept only; the state encoding is undecided. After every reset:

`RESET → INITIALIZING → CONFIG_REQUIRED → CONFIG_VALID → READY`

- **CFG-1** Reset invalidates the profile's configuration-valid state *even if physical configuration registers retain values*. The existing RTL does not reset the Padé coefficient memories (`rplu_thimble_pade.v` uses initial values and clocked writes with no reset branch); this contract never assumes asserting reset produces known coefficients.
- **CFG-2** Rehydration is **host-driven**, through `0xA5`: no autonomous coefficient loader. Until CONFIG_VALID, the engine rejects instructions (not-ready kind, with the sub-state visible, so the host can tell boot hydration, configuration-required and boot FAULT apart).
- **CFG-3** **Transport-available versus execution-ready.** The SPI interface (configuration writes, record and status reads) MUST remain usable while the engine is not execution-ready, so the host can upload coefficients. Only instruction execution is gated by READY.
- **CFG-4** The hardware tracks completion of the required configuration *write sequence* (every register or table entry the frozen set requires, each received with a valid CRC and header), not only the first write.
- **CFG-5** Transfer is not validity. Completion of the sequence proves the configuration was transferred, not that its values are the supported ones. The profile supports **one frozen coefficient set**, identified by an independently recorded hash. How the hardware establishes identity (a comparison against a stored copy, a hash/CRC check of the received values, or a host-only assertion) is open (D13); a host-only assertion would not protect against a misconfigured host.
- **CFG-6** A `0xA5` write that changes profile-covered configuration after CONFIG_VALID returns the engine to CONFIG_REQUIRED until re-verified, so an operation can never run with a partially updated configuration. Writes are accepted only while idle (INV-10).
- **CFG-7** Reset during a staged coefficient pair (the low/high half-writes), or during an operation, discards the staged data and invalidates configuration. The host re-establishes configuration after every timeout-and-reset.
- **CFG-8** The registers and tables that make up "the profile's configuration" (Padé numerator and denominator coefficients, BTU rows, kappa and any others that influence `0x2A`) are to be enumerated for the frozen set (D14). QR contents after reset are defined by the numerical contract (§10), not by this clause.

This is deliberately small: a deterministic host-driven sequence, not a bootloader or a dynamic configuration manager.

## 4. Vocabulary, safety and liveness

> **Safety:** no accepted instruction produces more than one terminal outcome, and no refused or unsupported instruction publishes a fresh valid result.
> **Liveness (conditional):** an accepted instruction eventually completes, provided clocks continue, reset does not intervene and the profile's execution assumptions hold (§6, LIVE-1).

| Term | Definition (proposed) |
|---|---|
| **Submitted** | A frame carrying an instruction word reached the ingress. |
| **Transport-rejected** | Not delivered to the engine (CRC failure, malformed header, aborted frame). |
| **Rejected at acceptance** | Delivered but not taken: engine not execution-READY, a transaction outstanding, or (configuration) not idle. |
| **Accepted** | Execution ownership transferred to the engine. CRC success is necessary, not sufficient. |
| **Completed** | The accepted transaction reached its terminal outcome and its record is published. |
| **Succeeded / Refused / Unsupported** | Outcomes SUCCESS, REFUSED (execution ended without publishing an invalid result, e.g. A31 zero-divisor), UNSUPPORTED (opcode or operand outside the supported set; no effect). |
| **Result telemetry** | A host-visible result published with a lane label. Distinct from an architectural QR write (§7). |

`inst_done` MUST NOT be read as success. The existing port MAY remain as an internal completion input, with outcome, result and effect-commit timing supplied separately; it is asserted today for unsupported opcodes.

**Invariants (proposed).**

1. **INV-1 At most one terminal outcome** per accepted instruction; none for a cancelled transaction.
2. **INV-2 Single outstanding, enforced by hardware.** Outstanding runs from acceptance until the record is published and the required effects are committed, across the core and everything behind the ingress. A second instruction is rejected visibly, independent of host behavior.
3. **INV-3 Rejected traffic is inert.** A rejected instruction or configuration write never alters, delays or discards an in-flight operation's step, result or record, including a rejection coincident with a completion.
4. **INV-4 No fresh-valid on refusal.** REFUSED and UNSUPPORTED transactions raise no result-valid, commit or telemetry update, and never present a previous result or an undefined value as fresh, including after reset. No late publication after cancellation.
5. **INV-5 Authorization is classified and latched at acceptance.** One shared profile predicate (supported opcode, and for ROTC the angle set) is evaluated once, when the instruction is accepted. The result is latched with the transaction. Every instruction-caused initiation and side effect, over the protected-state set of §9, is gated by *that transaction's* latched authorization for its whole lifetime, not by the current value of the incoming word. A later rejected word MUST NOT suppress or gate the accepted operation's execution, completion or publication. Configuration writes (`0xA5`) are governed by their own idle rule (INV-10), not by an opcode predicate. Activity not attributable to the transaction (§9) is unaffected.
6. **INV-6 Rejections are visible, distinct and fresh** (§8).
7. **INV-7 Distinct consecutive transactions** are distinguishable even with identical results.
8. **INV-8 Record stability and coherence:** a published record is stable until the next acceptance or reset; its fields are mutually coherent.
9. **INV-9 Transport status is separate from arithmetic status.**
10. **INV-10 Configuration is immutable while a transaction is outstanding.** Configuration writes are accepted only while idle; otherwise rejected visibly (configuration-while-busy) and nothing is written.
11. **INV-11 Publish after commit.** SUCCESS is published only once the instruction's specified architectural effects and result telemetry have committed. The write enable, commit telemetry and `inst_done` are set together, but the QR register file samples its registered write enable on the following clock; the controller therefore publishes no earlier than that commit point. Signal names are not evidence of atomicity. A reset coincident with a commit boundary wins: the transaction does not complete (§5).

## 5. Event ordering and records

**Two kinds of host-visible record (semantic model, not a layout).**

| Record | Updated when | Content (semantic) |
|---|---|---|
| **Transaction record** | An instruction is accepted; then completed | identity; state (executing / completed); terminal outcome; result-valid; result telemetry (zero or one payload) |
| **Rejection record** | A submission or configuration write is rejected | rejection identity (its own); kind; command class if known |

Both are in a defined "none yet" state after reset.

**Ordering rules (proposed).**
- **Reset overrides both records.** Otherwise the two records update **independently**: a completion and a rejection on the same edge update both records, and neither suppresses the other. No accepted request is lost and no rejection identity is skipped.
- **Acceptance decision** uses the registered outstanding state before the edge. A request sampled on the edge at which a completion publishes is evaluated against the pre-edge state and is rejected as busy; this is the rule the H0-V1 windows (swallow at the completion cycle) must now satisfy visibly.
- **Same-edge accept and complete** (an instruction that finishes without an observable executing cycle): publish the new identity in the completed state with the committed result. The "executing" state may never be observed. Outstanding ends only after atomic terminal publication and effect commit (INV-11).
- **Read snapshot:** a read command captures both records at one defined snapshot point and returns that coherent snapshot. Precedence among simultaneous acceptance, completion, rejection, read and reset follows the rules above; it is not a single priority multiplexer.

## 6. Polling, liveness, timeout and reset

**Host polling discipline (proposed; single host owns the interface).** Before submitting, snapshot both the transaction identity T0 and the rejection identity R0. Submit. Poll until either (a) the transaction identity differs from T0 and the record shows completed, or (b) the rejection identity differs from R0. A new rejection after a submission is attributed to that submission (single host, one submission in flight). If neither appears within the timeout, the outcome is unknown (below). For a configuration write, poll the rejection identity (a valid write produces no transaction record).

**Counter wrap and bounded loss.** The rejection record keeps the latest kind and a generation counter. The host reads after every submission, so at most one rejection is unobserved per submission; detection of multiple unobserved events requires fewer than the counter's modulus of unobserved events, and the host then cannot recover their kinds (bounded loss: latest kind retained, count preserved modulo its width). Events beyond the assumed discipline (unsolicited traffic, a competing issuer) are outside the contract. Widths are open (D2).

- **LIVE-1** If clocks run, reset does not intervene and the profile's units terminate, an accepted instruction completes. The completion bound for each supported instruction is a profile property to be established; the core-level simulation latencies (QLDI 2 cycles, QSUB 4, ROTC 6, `0x2A` 556) are samples, not bounds.
- **Reset** cancels the outstanding transaction. After reset both records are in the "none yet" state, configuration is invalid (CFG-1), and boot gating applies; a transaction in flight at reset is not completed, no record claims it, and no late event from the cancelled engine may publish (the engine is reset, not abandoned).
- **Host timeout** is not an architectural outcome and MUST NOT be reported as REFUSED. The host treats the transaction as outcome unknown, resets, re-establishes configuration (CFG-7) and reads the "none yet" state before submitting. v0 defines no hardware watchdog.

## 7. Outcome semantics and results

Four things are kept distinct: **architectural QR state mutation**, **host-visible result telemetry**, **instruction completion** and **arithmetic refusal**.

| Instruction | Architectural effect | Result telemetry (zero or one) | Publication point |
|---|---|---|---|
| QLDI | QR lane written | commit of the destination lane (one) | after the QR write commits (INV-11) |
| QSUB | QR lane written (two-cycle sequence) | commit of the destination lane (one) | after the write commits |
| ROTC | QR lane written after the rotor completes | commit of the destination lane (one) | after the write commits |
| `0x2A` | **none**: no QR register write | A31 limbs with a lane label (one) | after the telemetry commit |

`0x2A` returns host-visible telemetry; the lane label names the destination associated with the result and is **not** a QR register write. A later QSUB or ROTC cannot consume the `0x2A` result by naming that lane. If a future design writes Padé results to the QR file, that is a separate architectural decision with its own conformance tests. **The simulator must reflect this distinction.** The baselines produced exactly one commit per supported instruction; this is recorded as an observation, with exact payload layout left to the numerical contract. DELTA-style state effects without telemetry are excluded.

- **SUCCESS:** specified effects committed; result-valid true with that one telemetry item.
- **REFUSED:** terminal, no commit. In this profile, arithmetic refusal of `0x2A` (A31 zero divisor): the consumer classifies `pade_done && flags_v` as REFUSED and `pade_done && !flags_v` as SUCCESS. This addresses the A31-R2 witness only; it is not a proof that every failure is detected. Other error events (`rns_error`, quadray-coherence fault, pipeline stall, busy) are not assumed to be refusals: each must be classified per profile as terminal, diagnostic or transport-level, with priority and late-event handling, and associated with the owning transaction (D7). The multiple-result concern for the RPLU2 pipeline is narrowed by the one-hot BTU input of this configuration; this is an assumption to be confirmed in the exact image, not a counterexample.
- **UNSUPPORTED:** terminal, no effect over the protected-state set, no telemetry.
- A refusal may leave physical registers holding old data; that data is never associated with the new transaction or flagged valid.

## 8. Rejection kinds and transport policy

| Case | Policy |
|---|---|
| CRC mismatch on a recognized `0xB1` or `0xA5` frame | Transport rejection, CRC kind; existing `0xAC` CRC sticky preserved. |
| `0xA5` frame whose CRC matches but whose header byte is not `0xA5` | Transport rejection, **malformed-header kind** (distinct from CRC mismatch); the legacy CRC sticky is still set, as today, for existing hosts. |
| Recognized `0xB1`/`0xA5` that is cut off (CS dropped, deadman) before the frame completes | Transport rejection, abort kind. |
| CS asserted and the command byte incomplete or not B1/A5 | Not classifiable as an instruction or configuration frame: no rejection event, no effect on any record. |
| Valid instruction while not execution-READY | Rejection, not-ready kind (with sub-state, §3); not replayed. |
| Valid instruction while a transaction is outstanding | Rejection, busy kind; outstanding transaction unaffected. |
| `0xA5` write while not idle | Rejection, configuration-while-busy kind; nothing written. |
| Reset during a frame | Frame discarded; records reset. |

**"Recognized"** means the 8-bit command byte decoded as `0xB1` or `0xA5` while CS stayed asserted, assuming the SPI mode-0 alignment the slave expects. A frame whose bit alignment is corrupted decodes to whatever byte results and is classified accordingly; no stronger claim is made. Boundary cases (CS drop or deadman on the last bit, timeout concurrent with the final CRC bit) are acceptance tests (AC-7).

## 9. Protected state and background activity

**Protected-state set P** (every effect on these is gated by the transaction's latched authorization): Quadray register contents and tags; commit telemetry (`qr_commit_*`); result outputs, including the HEX outputs and the ROTC debug word; configuration registers (Padé coefficients, BTU rows, kappa) and their staging; rotor, pipeline and SOM start strobes; the Artery output port; REGEN counter and chain inputs (`regen_eligible_op`, `chain_op_strobe`) and the chain state; the DELTA/QR write enables; any autonomous trigger caused by an instruction. **Background activity** unrelated to the transaction (hydration sweeps, the autonomous stability network, audio and similar clocked blocks) is not attributed to the instruction, is not gated by it, and is out of the "no effect" claim; the profile image enumerates which blocks exist.

## 10. Numerical-semantics contract (mandatory prerequisite)

A **separate numerical-semantics contract** for QLDI, QSUB, ROTC and `0x2A` is a mandatory prerequisite for H0 profile qualification. It is not written here. Transport review may proceed independently; the transport contract and the numerical contract are separately testable (transport tests depend only on accepted, completed, outcome and rejection, not on values). A transaction record does not establish numerical correctness or simulator parity.

| Operation | Qualification focus (source facts to resolve) |
|---|---|
| QLDI | Immediate decoding and sign extension, register-lane selection (`qr_lane` wraps an 8-bit index modulo 13), scale and canonical representation (boot hydration uses Q12 `0x1000` per unit; QLDI loads unscaled integers) |
| QSUB | Operand interpretation, arithmetic width (the two 32-bit halves subtract independently), truncation and result state |
| ROTC | Supported angle encodings, exact transformation, 32-bit sums and divide-by-three without an explicit zero-remainder or overflow refusal, committed state |
| `0x2A` | Input interpretation, narrowing of coefficient halves to 18 bits, Padé arithmetic, refusal, telemetry format and lane label |

Angles 0-5 are the conservative candidate set; the other angles are UNSUPPORTED in the profile until their own evidence is adequate. Ratification of the mathematics and its fixtures precede any conformance claim.

## 11. Relationship to existing SPI commands

| Command | Treatment (proposed) |
|---|---|
| `0xB1` | Command value, framing, big-endian word and CRC unchanged. CRC success is necessary but not sufficient for acceptance. The strobe becomes an internal request that is accepted or rejected, never silently dropped. |
| `0xA5` | Framing unchanged. Writes are accepted only while idle (INV-10); a write during an outstanding transaction is rejected visibly. This changes behavior for a legacy host that writes coefficients during an operation (the prior behavior could corrupt that operation). |
| `0xAC` | Command value, byte layout, documented field meanings and clear/sticky behavior unchanged; its spin-dependent debug meanings are not reused as completion or outcome. Use of spare byte-3 bits is open (D4). |
| `0xAE` | Same command, layout and sticky "last commit" meaning; its valid byte MUST NOT be the only freshness evidence. After the refusal fix the latch is updated only by SUCCESS telemetry. |
| Record read | An **additive** mechanism (for example a new read-only command) is the compatibility-preserving direction; no value or layout is assigned. |

**Compatibility wording.** For existing hosts the command values, framing, field meanings and documented clear/sticky behavior are preserved. Response *values* may change where invalid prior behavior is repaired: an A31 refusal no longer produces a fresh commit (so the first-after-reset refusal no longer leaves `0xAE` valid with undefined data), and `0xA5` writes during an outstanding transaction are rejected. Status fields are spin-dependent; no particular spin's value is generalized.

**Real SPI timing is UNVERIFIED (qualification blocker).** H0-V1 results are core-level. A `0xB1` frame is at least 80 SCK bit periods, but the relationship between SCK, `clk_fast` (`A7_CLK_DIV_LOG2`, spin dividers) and the slave's three-sample synchronizer limit is not established. No ratio is assumed and no collision window is claimed reachable on the board. The contract requires hardware rejection (INV-2, INV-3) regardless of reachability. No buffering is proposed.

## 12. Verification acceptance criteria (proposed, finite)

Two classes: **core-ingress injection** (clock-level stimulus at the shared ingress/engine interface, exhaustive over the stated offsets) and **SPI integration** (serialized frames at explicitly identified operating points). Held-valid means *one* request held high for several cycles: exactly one acceptance or one rejection, not a series of rejected packets. Gap 1 in H0-V1 is that held-valid behavior. The H0-V1 and A31-R2 probes are starting fixtures; the unsupported-opcode QR hash is a sample, not state proof.

| ID | Criterion |
|---|---|
| AC-1 | Each supported instruction alone (QLDI, QSUB, each angle of the final ROTC set, `0x2A`): one acceptance, one record with SUCCESS, result-valid, and the expected state and telemetry. |
| AC-2 | Opcode classes: all 256 opcode values with a canonical operand pattern; and per class of operand field the boundary values {all zero, all ones, unused/reserved bits set}, lane-index classes {0, 12, 13, 127, 255}, QLDI immediate sign classes, and ROTC angle classes {the final set, 6-35, 36-63} with unused-bit patterns. Each unsupported case: one UNSUPPORTED record, no telemetry, no change over P (§9). |
| AC-3 | Core-ingress: a second instruction at every cycle offset within each supported instruction's window (QLDI, QSUB, ROTC; `0x2A` over its full latency plus margin) and held-valid: rejected visibly as busy; the outstanding transaction completes with the correct result and exactly one record. A rejected unsupported word during an authorized operation does not gate it (INV-5). |
| AC-3b | Simultaneous completion and rejection: both records update independently; no rejection identity skipped; acceptance decision against pre-edge state; same-edge accept-and-complete publishes the new identity in the completed state with the committed result. |
| AC-3c | `0xA5` write at every offset during an outstanding transaction: rejected visibly, nothing written, the operation sees one configuration; a write while idle succeeds and a legacy host's idle write is unchanged. |
| AC-4 | A31 refusal after a success and first after reset, through the core path in this profile: REFUSED, no result-valid, no telemetry, no stale or `x` value; a following valid transaction succeeds; simultaneous error/done and other classified events (D7) behave as classified; no late publication. |
| AC-5 | Consecutive identical instructions give distinguishable transaction identities; consecutive identical rejections give distinguishable rejection identities; rollover and the reset state behave as specified; the dual-identity polling rule of §6 attributes correctly, including wrap. |
| AC-6 | Not-ready: rejected visibly with its sub-state (boot hydration, configuration required, boot FAULT distinguishable), not replayed. |
| AC-7 | Bad CRC, malformed `0xA5` header with valid CRC (legacy sticky preserved), recognized-B1 and recognized-A5 aborts, an unclassifiable fragment, CS drop or deadman on the last bit, timeout concurrent with the final CRC bit, and reset at each frame phase: classification per §8; no acceptance, no effect; existing `0xAC` CRC sticky unchanged. |
| AC-8 | Record stability: repeated reads (including across CS toggles) return one coherent snapshot of both records; reads during each update and simultaneous read/completion, read/rejection, acceptance/rejection and reset follow §5. |
| AC-9 | Reset during execution, during a staged coefficient pair and while an instruction is idle; host timeout followed by reset: no record claims completion, no late event, defined post-reset state, configuration invalid until rehydrated, resynchronization works. |
| AC-10 | Compatibility: framing and field semantics of `0xB1`, `0xA5`, `0xAC`, `0xAE` unchanged; unaffected successful transactions give byte-identical legacy responses; legacy `0xAE` retention after a refusal matches the corrected behavior of §11; `0xA5` idle writes unchanged. |
| AC-11 | A finite, named set of SPI/clock operating points (SCK, divider, phase offsets, CS setup/hold) fixed at qualification, with synchronizer margin measured; the serialized cases of AC-1 to AC-10 run at each. |
| AC-12 | Synthesis and timing of the exact image, then the supported, physically reachable suite on the board with preserved logs, build manifest and a hardware-evidence entry. Simulation, timing and physical results are reported as separate evidence levels. |
| AC-13 | Configuration lifecycle: reset → configuration required → rehydration → valid → READY; instructions rejected before valid; a `0xA5` change after valid returns to configuration-required; the frozen set's identity check passes for the recorded set and fails for a perturbed set; execution never runs on a partial configuration. |
| AC-14 | Commit before publish: a QLDI/QSUB/ROTC record is never published before the QR write has committed; reset at the commit boundary leaves no completed record; a following instruction sees the committed state. |
| AC-15 | `0x2A` telemetry: exactly one terminal record; telemetry only, no QR register-file write; the result is associated with its record across consecutive operations; no late results; the one-hot BTU assumption is confirmed in the exact image. |
| AC-16 | Elaboration check that disabled REGEN removes its counter **and** the chain instance (or that both are explicitly gated), and that the image enables only the profile's listed blocks. |

## 13. Remaining architectural decisions (owner / independent review)

Resolved by owner decision: configuration after reset (mandatory host-driven rehydration, §3), the numerical contract as a prerequisite (§10), `0x2A` as telemetry-only (§7).

- **D1** Record owner and wiring: the Artix-7 top is the natural owner; each included engine needs explicit accepted, terminal, outcome and result-event signals.
- **D2** Transaction-identity and rejection-generation widths, wrap and reset state.
- **D3** Exact edge definitions beyond §5 (pre-edge versus post-edge for each included instruction).
- **D4** Spare `0xAC` bits versus an additive record command; tying `0xAE` content to the completion (freeze until consumed, or carry the payload in the record).
- **D5** Location of the shared classifier and its latching, kept equal to the build's enable parameters.
- **D6** The final ROTC angle set (0-5 candidate).
- **D7** Classification of non-inverter error events as terminal, diagnostic or transport-level.
- **D8** Rejection record: latest-only plus generation versus per-kind sticky/overrun indicators.
- **D9** The legacy `inst_done` port (internal completion input versus removal).
- **D10** Build configuration of the profile (CUSTOM versus a new spin, REGEN disable at the top, `fpga_chain` handling, listed-peripheral set, timing closure).
- **D11** Completion bounds per supported instruction and the derived host timeout.
- **D12** SPI timing relationship and the operating-point set.
- **D13** How configuration identity is established in hardware (stored copy, hash/CRC of received values, or host assertion).
- **D14** The enumerated contents and recorded hash of the frozen configuration set (Padé coefficients, BTU rows, kappa, others).
- **D15** Encoding and visibility of the lifecycle states and of the transport-available versus execution-ready distinction.

## 14. Out of scope

New instructions or mathematical changes; a queue or sequencer; a bootloader or dynamic configuration manager; a unified FLAGS register (see SNAP-1); A31 arithmetic redesign (the repair is validity propagation, not arithmetic); choice of SPI encodings, counter widths or buffering; SPU-4; DELTA, HEX, REGEN, IROTC, SOM, Surd, SU3, Lucas and Neuro semantics; the numerical-semantics contract itself.
