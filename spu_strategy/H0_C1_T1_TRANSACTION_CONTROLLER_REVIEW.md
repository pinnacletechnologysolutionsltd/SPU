# H0-C1-T1 transaction-controller design review

**Verdict: REVISE; production implementation HOLD.** Source review only, against commit `2a9a9f12760bb13fb47bcf192b66f44645f35ef9`; no simulation, synthesis, or physical evidence was produced. H0-C1 revision 6 is a non-normative proposal, not implemented or qualified. This review concerns only its proposed Artix-7 SPU-H0-RPLU2-v0.2 profile; it does not establish general SPU semantics. The review identifies a feasible integration boundary, but the interface and unresolved contract details below must be frozen before production implementation.

## Verified baseline path

In `hardware/rtl/peripherals/io/spu_spi_slave.v`, synchronized SCK/CS/MOSI are sampled in `clk`; on a CRC-valid B1 frame the slave registers the big-endian 64-bit word and pulses `inst_valid`. CRC failure sets the existing sticky error. There is no acceptance handshake on this output. In `hardware/boards/artix7/spu_a7_top.v`, `spi_inst_valid` is dispatched to the core unless a Lucas, SU3 or Padé sidecar claims it. Core and sidecar completion/commit signals are combined; the selected commit is fed back to the slave. In `hardware/rtl/core/spu13/spu13_core.v`, `inst_accept = eff_inst_valid && !inst_seen && !surd_busy`, gated by boot readiness, but not by a whole-engine transaction interlock. The core's `inst_done` is a pulse, not a success outcome. QLDI/QSUB register the QR write enable, telemetry and done together; the QR file consumes the registered write on a subsequent edge. RPLU2 result-valid directly produces commit telemetry and done; it is not a QR write. The SPI slave retains the most recent commit for `0xAE`, without transaction freshness. These facts do not establish board SPI timing or a working H0 image.

The top runs SPI, dispatch and core in `clk_fast` and uses `rst_n_int`, generated from the physical reset pad by synchronization and a hold counter. External SPI pins cross into that clock through slave synchronizers; the controller need not introduce a second engine clock domain. The exact SCK/clock ratio, synchronizer margin, frame-end/CS ordering and deadman coincidence remain unverified. The top ties core `boot_done` high; hydration still precedes `core_boot_ready`. Existing named spins do not match the proposed enable set, and top does not pass `ENABLE_REGEN`; the core's chain remains instantiated outside the REGEN generate. These require explicit image/elaboration treatment, including autonomous behavior.

## Proposed integration and event interface

```text
 asynchronous SPI pins
        | synchronizers / frame parser (clk_fast)
        v
 B1 request, A5 request, transport reject -----> H0 controller
                                                   | lifecycle + manifest verifier
                                                   | accepted authorized word/config
                                                   v
                                           profile core / RPLU2
                                                   | terminal, outcome, commit
                                                   v
                           coherent transaction + rejection + lifecycle snapshots
                              | additive read       | success telemetry
                              v                     v
                           SPI reads              legacy 0xAE
```

Place one controller at the Artix-7 dispatch boundary, before any core/sidecar initiation and before configuration mutation; use a separately scoped module instantiated by the top, with parser extensions only for complete-frame/error events and coherent snapshot reads. For the H0 image, exclude the named sidecars and sequencer rather than relying on their claim mux. The existing general-purpose spins must retain their existing paths. This location can enforce one outstanding transaction across all included engines and independently record rejections while a completion occurs. A simple wrapper alone is insufficient: the core and RPLU2 must expose actual terminal classification and effect-commit timing, and all protected starts/effects must be gated by latched authorization, including chain and background triggers.

Proposed synchronous interface: request-valid plus full word and request-class; distinct accept and reject events with rejection kind; selected manifest and complete configuration identity/value, commit acknowledgement and lifecycle/progress; latched transaction identity and authorization; explicit engine terminal event with outcome/reason, result-valid and payload/lane, plus architectural commit event or an equivalent proven publication delay. Transport parser reports CRC, malformed-header and recognized abort independently. A held request must be consumed once. Snapshot both records and lifecycle atomically at read start; reset or CS interruption ends/invalidates the read. Do not derive success from `inst_done`, incoming word, or sticky `0xAE` valid.

Canonical decode must use the frozen per-opcode fields and enable parameters: QLDI, QSUB, ROTC angles 0/2/5 and 0x2A only, with lane bounds and reserved fields checked before any effect. A READY, idle but noncanonical word is **accepted then completed UNSUPPORTED**, not an acceptance rejection. Latch the decision and identity at acceptance. Busy or not-ready requests are rejected and cannot affect the active operation. Configuration checks must include the full selector/material/address/subfield and expected data, reject before staging, enforce ordered SET-N/SET-R writes and clear sequence progress on violation; a low coefficient half alone does not advance committed progress. The implementation must expose an acknowledgement that distinguishes staging from the committed pair. Manifest contents and selection are not yet frozen.

```text
 RESET -> INITIALIZING -> CONFIG_REQUIRED -> READY/IDLE
                              ^                  |
                              | configuration    | accepted instruction
                              | invalidation      v
                              +------------ EXECUTING -> COMMIT/PUBLISH -> READY/IDLE
```

This is a conceptual state machine, not an encoding. Separate record update logic permits simultaneous rejection and completion; pre-edge busy state decides admission. Reset wins over all events, cancels work and invalidates records/configuration/staged halves; prove no late event after reset. Publication waits for QR write commit, or for 0x2A telemetry commit, and atomically binds identity, outcome, validity and payload. Accepted unsupported may complete on its acceptance edge under the contract's same-edge rule. Host timeout is unknown outcome and requires physical-reset recovery; it is not an engine outcome or implicit reset. Identity is reset-scoped; widths, wrap/loss limits and host resynchronization remain decisions.

For future `rplu2_domain_refused`, treat it as an explicitly transaction-associated terminal REFUSED/NUMERIC_DOMAIN input, after checking all eight original signed 32-bit coefficients against [-9457,9457] before narrowing or starting SOM. This signal is absent in the reviewed baseline; do not infer it from a result-valid pulse. Separately propagate the characterized Padé `done && flags_v` refusal, suppressing stale result telemetry and 0xAE updates. Other integrity faults remain unclassified and must never be silently labeled success. Prove one terminal event and no late result for either refusal. The numerical contract and exact SET-N/SET-R evidence remain prerequisites.

Preserve B1 framing/CRC and `0xAC` layout, meanings and sticky/clear behavior; keep `0xAE` as sticky last successful commit, with refusal retaining historical data. Add coherent read-only reporting for transaction/rejection records, lifecycle and progress without assigning command values or bit layouts here. A5 framing remains but its allowed behavior intentionally narrows under H0. Response values can change where invalid commits are repaired. Parser error visibility and same-edge priority require design work; existing CRC sticky alone cannot distinguish all required rejection kinds.

## Minimal externally testable stages

1. Freeze full image parameters, canonical field masks, both configuration manifests, event interfaces, record generation/wrap rules, reset and snapshot priorities, fault classifications and timing assumptions. Review REGEN/chain and all background blocks. No architectural qualification follows from this stage.
2. In an isolated profile, implement and test parser event reporting, acceptance/interlock, latched authorization and independently updated records using a controlled engine endpoint. Exercise held-valid, busy, unsupported, simultaneous completion/rejection, reset and snapshot interruption, including serialized B1/A5/AC/AE compatibility.
3. Integrate configuration gating and committed-pair acknowledgements; test sequence violations, all disallowed targets, initialization, busy writes, reset and SET-N/SET-R recovery. Integrate core commit/terminal signals and test QR commit-before-publication and result freshness, including prior-success then refusal and refusal first after reset. Test domain boundaries and A31 refusal with actual pipeline configuration.
4. Run the finite H0-C1 acceptance suite at frozen SPI operating points, then separately report simulation, exact-image synthesis/timing and physical board evidence. Qualify numerical semantics and candidate angles separately. No timing or silicon claim is made here.

## Decisions and blockers

Resolve H0-C1 D1–D16, particularly canonical masks and same-edge commit semantics; counter widths and bounded-loss host protocol; manifest identity/selection and full allowlist; fault outcomes; exact enabled background/chain behavior; per-instruction completion bounds; board reset availability; SPI timing and snapshot implementation. Confirm the one-hot BTU assumption and that no excluded sidecar or autonomous path bypasses the controller. Until these are frozen and the draft independently reviewed, the proposed implementation remains HOLD.
