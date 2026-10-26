# Engineering Contract: GPU T1r Per-Primitive Palette-Pair Selection Q0

**Date:** 2026-10-01  
**Contract ID:** `gpu_t1r_palette_pair_q0_2026-10-01`  
**Status:** DRAFT — design freeze proposal only; no RTL, build, or hardware execution authorized

## 1. Objective and Scope

Define T1r as the T1q material-result path with a packet-selected RGB palette pair for each of the four winning primitives. T1q computes a Boolean result from the winning primitive's selected predicates and four-bit truth table. T1r maps result `0` or `1` to that primitive's corresponding three-bit RGB color.

The T1q fields and semantics remain byte-for-byte unchanged. T1r adds four palette bytes to the existing 182-byte T1q scene payload:

| Scene payload byte | Wire byte including `A5` | Meaning |
|---:|---:|---|
| 0..173 | 1..174 | Existing T1q scene data |
| 174..177 | 175..178 | Four per-primitive truth-table nibbles; values `0x00..0x0F` |
| 178..181 | 179..182 | Four per-primitive predicate selector bytes |
| 182..185 | 183..186 | Four per-primitive palette-pair bytes |

The T1r payload is exactly 186 bytes; the complete serial frame is exactly 187 bytes including the start byte. Each palette byte is encoded as:

```
bit 0 = outcome-0 red
bit 1 = outcome-0 green
bit 2 = outcome-0 blue
bit 3 = outcome-1 red
bit 4 = outcome-1 green
bit 5 = outcome-1 blue
bits 6..7 = reserved; must be zero
```

RGB bits are expanded to the existing four-bit channel buses by replication (`4'b0000` or `4'b1111`). An invalid winning fragment remains black. The color pair is selected using the same registered winning-primitive index and activation generation as the corresponding truth-table and predicate-selector bytes.

T1r is a separate compile-time profile. Enabling it enables T1q truth-table and predicate-selector semantics internally; it must not require the T1q profile flag to be enabled simultaneously. Existing T1q and earlier profile parameters, packet lengths, validation, and outputs remain unchanged when T1r is disabled.

## 2. Q0 Design Invariants and Halt-and-Flag Review

- The palette maps only the final T1q Boolean result to RGB. It does not change primitive coverage, winner selection, predicates, selectors, or truth-table bit order.
- Palette bytes are indexed by primitive slot, not by screen position or truth-table input.
- Each palette tuple must come from the same active scene generation as the selected truth table and predicate selector. No candidate-scene field may leak into active rendering before scene activation.
- Scene-loader validation must independently enforce T1q table bytes `<= 0x0F` and T1r palette bytes `<= 0x3F`.
- **Pre-execution hazard:** `spu_scene_loader` currently has one validation window and one shared maximum-byte value. Reusing that single maximum cannot validate both T1q and T1r field constraints. The implementer must add a second independently parameterized validation window and maximum, or halt and flag if preserving the current loader/profile behavior requires a broader change. Do not weaken either field's reserved-bit validation.
- The additional scene storage is 32 bits. Confirm the receiver count width, scene-bank dimensions, profile unpack wiring, board wrapper parameters, synthesis source lists, and build profile/tag allowlists before implementing.
- The one-bit-per-channel board output exposes eight RGB colors. Do not claim higher color depth from the four-bit internal channel buses.
- The current T1q visual evidence covers its frozen A/B/C/A sequence only. It does not establish T1r palette selection.

### Read-only pre-review findings (2026-10-01)

| Review item | Source finding | Q1 disposition |
|---|---|---|
| Receiver/count width | `spu_scene_loader.payload_count` is 8 bits and compares against `PAYLOAD_BYTES - 1`; this represents indices 0..185. The exposed `diag_payload_count` is only 7 bits in the loader, GPU top, and board wrapper, so it truncates counts above 127. | The receive counter is wide enough. Widen the diagnostic count to 8 bits end-to-end if Q1 relies on observing the full T1r count; otherwise state that the diagnostic count is not used as evidence. Keep packet length exact at 186 payload bytes. |
| Two validation windows | The loader currently has one `[start, start+bytes)` comparator and one shared `FINAL_BYTE_MAX`. T1q supplies start 174, length 4, max `0x0F`. | A second window with its own start, length, and max is a bounded extension. Give the new parameters disabled defaults and preserve the existing window/trailing-byte behavior for every old profile. For T1r configure the existing table window as `174/4/0x0F` and the palette window as `182/4/0x3F`. Invalidity from either window must block commit, including when the invalid byte arrives on the final payload cycle. This is structurally reviewable but not simulation-proven. |
| Winner/activation alignment | The existing material-op and predicate-selector selectors both use the registered `partition_winner_id`; on `activate_scene` they select from candidate bytes on that same edge, otherwise from active bytes. The registered U/V and valid-fragment path also advances on that edge. | Implement palette selection with the same candidate-on-activation/active-afterward rule and winner ID. This can follow the existing one-register selection pattern without adding a pipeline stage. Cycle alignment remains unproven until Q1 simulation exercises overlap and activation transitions. |
| Four-lane discriminator | Existing four-lane byte selectors define lane 0 in bits `[7:0]` through lane 3 in `[31:24]`. | Freeze distinct outcome-0/outcome-1 pairs for all four lanes and an oracle scene that forces both outcomes for every lane. Compare RGB per winning lane; a uniform palette or single visible outcome is insufficient. No packet/oracle is implemented in Q0. |

These findings remain part of Q0. They do not authorize a Q1 implementation contract or establish functional correctness, synthesis fit, timing closure, or hardware behavior.

## 3. Target Files for a Later Q1 Authorization

Expected implementation scope, subject to implementer pre-review:

- `hardware/rtl/gpu/spu_gpu_top.v`
- `hardware/rtl/gpu/spu_scene_loader.v`
- `hardware/boards/artix7/spu_a7_gpu_vga_top.v`
- `hardware/boards/artix7/build_a7.sh`
- T1q/T1r profile and GPU testbenches under `hardware/tests/`
- A deterministic T1r packet/oracle sender under `tools/`
- A T1r route/hardware contract under `spu_strategy/`, only after functional and route evidence

Keep newly introduced logic in single-purpose modules of 50–150 lines where a module boundary is needed. Do not refactor unrelated profile logic.

## 4. Required Functional Coverage for Later Q1

The Q1 test plan must falsify each of these properties:

1. For all four primitive slots, palette result `0` produces exactly its outcome-0 RGB bits and result `1` produces exactly its outcome-1 RGB bits.
2. All 16 T1q truth-table patterns still produce the existing truth-table result for all four `{pred_u,pred_v}` input combinations.
3. Per-primitive selector, truth table, and palette remain aligned with the registered winning primitive across adjacent pixels, overlapping primitives, and an activation edge.
4. An invalid fragment emits black regardless of its palette contents.
5. T1r accepts an exactly 186-byte payload only after all reserved bits validate; `0x40` in any palette byte and `0x10` in any truth-table byte prevent commit. A subsequent valid payload can commit normally.
6. T1q still accepts exactly 182 payload bytes with its existing validation and rendered blue/yellow result; no T1r-only bytes are consumed in that profile.
7. Profiles with T1r disabled retain their prior payload lengths, validation, and outputs.
8. No vacuous assertions: each relevant input must toggle, each output must be compared against a computed expected value, and winner/activation alignment must be observed across real state transitions.

Functional coverage is simulation evidence only. Synthesis/place-and-route, board transport, and operator-visible hardware evidence are separate gates.

## 5. Later Q1 Implementation Order

1. Run the implementer's halt-and-flag review against the current loader, profile guards, packet sender, and registered material path. If the review finds that the proposed 186-byte payload or two-window validation conflicts with an existing invariant, stop and update this contract before editing RTL.
2. Add the T1r profile as a default-off, mutually exclusive successor profile that selects T1q material evaluation internally.
3. Extend scene storage and byte count to 186 bytes only for T1r. Keep the T1q 182-byte configuration unchanged.
4. Add independent validation for the truth-table and palette windows. Reject malformed packets without activating the candidate bank.
5. Capture the winning palette byte alongside the winner-selected T1q selector/table tuple. Register and activate the tuple under the existing scene-generation rule.
6. Select the outcome-0/outcome-1 RGB bits from the registered palette byte using the registered T1q result; gate all channels with the existing valid-fragment signal.
7. Add the falsifiable tests in §4 and a fixed packet oracle covering distinct pairs on all four primitive slots.
8. Run the scoped simulation and repository gates in §6 only after the contract is separately authorized for implementation and verification.

## 6. Later Verification Commands (Not Authorized by This Q0 Draft)

The Q1 implementer must freeze exact test names and detached job budgets in an implementation contract before running these or any build command. Scoped commands should use the repository's registered T1r test prefix and include:

```bash
TB_FILTER=<registered_t1r_prefix> python3 run_all_tests.py
bash tools/verify_repo.sh
```

Any synthesis/place-and-route run exceeding 60 seconds must use `tools/run_detached_job.sh` with a new `build/` child, frozen timeout, and desktop notification. Do not interpret a detached run without exactly one durable `COMPLETE`, `FAILED`, or `TIMEOUT` marker. Hardware programming, UART, visual observation, and persistent flash are not authorized by this contract.

## 7. Evidence State and Stop Conditions

| Evidence claim | Current state |
|---|---|
| T1q truth-table functional behavior | Previously qualified under its own contract; no T1r implication |
| T1q route and bitstream | Previously qualified under its own contract; no T1r implication |
| T1q scaled operator observation | Recorded in `docs/hardware_evidence.md`; no T1r implication |
| T1r structural validity | NOT RUN |
| T1r functional simulation | NOT RUN |
| T1r synthesis/place-and-route | NOT RUN |
| T1r hardware observation | NOT RUN |

- If review identifies conflicting byte order, receiver sizing, profile aliasing, incomplete validation, or an activation-edge alignment ambiguity, halt and revise this contract before implementation.
- Do not change T1q behavior or the T1q payload while implementing T1r.
- Do not modify the build clock, timing constraints, or unrelated profile defaults under this contract.
- No T1r implementation, build, hardware programming, UART transmission, or visual claim is authorized by this Q0 draft.
