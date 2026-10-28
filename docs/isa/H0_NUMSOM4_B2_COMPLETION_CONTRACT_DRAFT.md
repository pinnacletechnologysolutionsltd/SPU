# NUM-SOM-4-B2 — RPLU2 numeric-domain refusal: completion-interface contract (DRAFT)

**Status:** non-normative draft; documentation only. Nothing here is implemented. Phase B production implementation is **HOLD** until this contract is accepted. It does not change [`H0_C1_PROTOCOL_CONTRACT_DRAFT.md`](H0_C1_PROTOCOL_CONTRACT_DRAFT.md) or [`H0_NUM1_NUMERICAL_CONTRACT_DRAFT.md`](H0_NUM1_NUMERICAL_CONTRACT_DRAFT.md).
**Basis:** `dev/next` at `949ffc5` (RTL as of Phase A, `9bbb7b698029ee38728bcc87ce39e82062adc0f8`); source review [`NUM_SOM_4_B1_INTERFACE_REVIEW_9bbb7b6.md`](../../spu_strategy/NUM_SOM_4_B1_INTERFACE_REVIEW_9bbb7b6.md). Findings there are source-derived, not observed waveforms.
**Question answered:** how can the core report an accepted numeric-domain refusal so that it is attributed to the right instruction and never mistaken for success?

## 1. Responsibilities

| Mechanism | Responsibility | Status |
|---|---|---|
| `inst_done` | Releases the instruction handshake. It never means success. | Existing |
| `rplu2_domain_refused` | Identifies an internal numeric-domain refusal for the instruction completing on the same cycle. | Proposed (Phase B) |
| Fresh-result evidence (`rplu2_result_valid` → `qr_commit_valid`) | Success only. | Existing |
| H0 transaction controller | Associates completion with the accepted transaction, latches outcome and reason, and publishes them to the host. | Not implemented (H0-C1) |

Adding the refusal event to the core does **not** make the refusal host-visible and does not satisfy H0-C1 on its own. On this baseline the SPI path has no completion input and no transaction controller; the top-level OR of `inst_done` with sidecar commits has no reader that could carry a reason.

## 2. Conceptual completion bundle (for the H0 controller; encoding not chosen)

| Field | Meaning |
|---|---|
| completion valid | an accepted instruction has reached its terminal event (core: `inst_done`) |
| outcome | SUCCESS, UNSUPPORTED, REFUSED / NUMERIC_DOMAIN, or the separate A₃₁ arithmetic REFUSED |
| fresh-result valid | true only for SUCCESS with a newly committed result |

Phase B implements only completion valid (existing) and one refusal indication. The outcome code and the fresh-result bundle are **future H0-C1 work**; no SPI reason encoding is chosen here.

| Case | `inst_done` | `rplu2_domain_refused` | fresh result (`qr_commit_valid`/`rplu2_result_valid`) |
|---|---|---|---|
| in flight | 0 | 0 | 0 |
| SUCCESS | 1 | 0 | 1 |
| numeric refusal | 1 | **1** | **0** |
| other acknowledged no-effect completions | 1 | 0 | 0 (distinguished only by the H0 controller) |

## 3. Local invariants for Phase B (testable at core level)

* **LI-1 Atomic completion.** For an instruction refused by the domain guard, `rplu2_domain_refused` is a registered one-core-clock pulse that is high on exactly the cycle on which `inst_done` is high for that instruction. It is never high without `inst_done`.
* **LI-2 No false success.** On a refused instruction no `rplu2_result_valid`, no `qr_commit_valid`, no QR write and no later output occurs. The refusal indication and any fresh-result indication are never high together. A previously held result (for example the SPI sticky `0xAE` valid) is historical and is not evidence about the refused instruction.
* **LI-3 One terminal event.** Each accepted canonical `0x2A` ends in exactly one of: start followed by one result (SUCCESS path), or one refusal. A failing guard clears `rplu2_som_pending`, emits one refusal and never asserts `rplu2_som_start`; only the passing branch asserts the start, exactly once.
* **LI-4 Guard location and order.** The guard samples the eight original signed 32-bit P/Q halves of `qrf_rd_A..D` at the edge where `rplu2_som_pending && !rplu2_busy` would launch, against `[-9457, 9457]` inclusive, before the 18-bit extraction is consumed. Combinational extraction may still toggle; nothing may consume it on a refusal.
* **LI-5 Stable operands.** The selected lane and its data must not change between the acceptance that selected the lane, the guard sample, and the pipeline's feature capture. This is a precondition on the driver (see LI-7), not something the core currently guarantees.
* **LI-6 Reset.** Reset cancels `rplu2_som_pending`, any start and any outstanding refusal. No refusal or start appears after reset, and a reset coincident with the guard edge wins (no event).
* **LI-7 Single outstanding (assumption, not a core guard).** `inst_accept` checks only `inst_valid`, `inst_seen` and `!surd_busy`; it does not protect the read lane, result label or the pending/start window. From acceptance through the terminal event and settled effects, exactly one instruction is outstanding. A core-only experiment enforces this in the test driver; the future H0 controller enforces it in the system.
* **LI-8 Collisions.** A refusal coincident with another completion (previous result, Surd retirement, sidecar commit, another instruction) is outside the contract and must not be relied on. Phase B tests include controlled collision experiments whose observed behavior is recorded as observation only; priority in the existing completion chain is not an arbitration guarantee.
* **LI-9 Ownership.** `inst_done_r` keeps its single owner (the main core process). The refusal register is driven only from the RPLU2 pipeline generate block, and the public `inst_done` becomes `inst_done_r | rplu2_domain_refused` as one continuous expression. It is high on the refusal cycle only because the refusal register is; `inst_done_r` being low on that cycle is a consequence of LI-7, not of the expression.
* **LI-10 Scope.** The guard and refusal exist only in the `ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_PIPELINE` branch; the indication is tied low in the config-only, disabled and legacy-SOM branches. Sidecar spins can claim `0x2A` before the core sees it, so the guard does not cover them; the H0 profile excludes them.
* **LI-11 Receiver.** The receiver samples on the core clock and is always ready. A receiver in another clock domain or one that can be unready needs a held event with acknowledgement, which is future H0 work.
* **LI-12 Integrity faults.** An ECC double error or other integrity event is not NUMERIC_DOMAIN; its classification is H0-C1 D7.

## 4. Handoff to H0-C1

The H0 transaction controller must: latch `{completion, refusal}` atomically with the accepted transaction identity; give refusal precedence over success; publish a coherent record with reason, identity and result-valid false; define reset, clock-domain and sidecar arbitration behavior; and keep NUMERIC_DOMAIN distinct from UNSUPPORTED, transport rejection and A₃₁ arithmetic refusal. H0-C1 §§4–7 already name the REFUSED / NUMERIC_DOMAIN outcome; this document only fixes the core-side contract that feeds it.

## 5. Local testability

The guard can and should be qualified at core level before any host-visible handling exists. Directed tests (from the B1 review): all eight coefficient positions at ±9457 and ±9458, signed 32-bit extremes, pre-narrowing aliases, valid mixed-sign inputs; pass launches exactly once; refusal exactly once with aligned `inst_done` and refusal, no SOM/BTU/Padé start, QR write or fresh commit; back-to-back transactions after completion; reset during pending, refusal and launch; coexistence with a prior sticky result; controlled collisions (LI-8); disabled/config-only generate branches and legacy SOM isolation; QLDI, QSUB and ROTC unchanged. Observe `inst_done`, the refusal, pending/start, selected QR data, pipeline activity, register writes and telemetry independently; require simulator exit status 0 as well as matching checks. Because QLDI and QSUB cannot load the Q halves of B, C or D, tests of those positions force values through the register file's write port.

## 6. Open items

Implementation and timing closure of the guard edge; the H0 transaction controller and acceptance/busy policy; reason encoding; sidecar exclusion or arbitration in the H0 image; A₃₁ refusal propagation; SPI freshness. None is established by this document.
