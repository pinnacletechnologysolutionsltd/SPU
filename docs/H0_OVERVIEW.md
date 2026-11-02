# H0 overview: experimental host-control layer for the Gen-1 Surd CPU

**Status: experimental, simulation only.** Nothing here is silicon-verified or
synthesized (no entry in [`hardware_evidence.md`](hardware_evidence.md)). H0 is the
control layer between a host and the execution hardware: load a program, validate
it, start one execution, and read results, without the host managing instruction
fetch, handshakes or reset sequencing. Implementation record and full limitations:
`research/h0_rtl_1f_r3/INTEGRATION.md`.

## Pieces and their evidence

| Piece | What exists | Evidence |
|---|---|---|
| Software model | `software/spu_host/h0_program.py`: load / verify / execute / result for one restricted 14-instruction program shape; `docs/H0_SW_2_PROGRAM_INTERFACE.md` | 5 unit tests in the release regression |
| RTL controller | `research/h0_rtl_1f_r3/`: two program banks, START ownership, reset sequencing, frontend, frozen Gen-1 core | RTL simulation: `run_focused.py`, 4 negative controls, independent arithmetic oracle |
| Transport (UART/SPI) | not implemented | none |

The software model and the RTL controller are separate. They expose different
operations (the model: load/verify/execute/result; the RTL: bank write,
validate/promote, START) and have **not** been checked against each other.

## Behaviour demonstrated in RTL simulation

- **Two banks.** Each holds 14 words of 64 bits. A candidate is written to the
  inactive bank and promoted only after a scan of the fixed instruction shape and a
  CRC-32 match; a failed replacement leaves the previous program intact. CRC-32
  detects accidental corruption only. It is not authentication.
- **Single owner.** An accepted START reserves ownership; competing START, load and
  promotion requests are refused until completion. A rejected START that stays high
  is not replayed later (negative control `replayed_start`). Non-preemptive.
- **Reset without losing the program.** START holds the execution domain in reset
  for at least two sampled clock edges, releases it synchronously, and enables
  fetch/issue only after initialization and core boot. The verified bank is kept.
  Two different programs (A, B) ran in sequence in simulation without any
  reconfiguration; no board has run this.
- **Results.** Six 32-bit slices, e.g. program A gives (13, 0, 4, 0, 9, 0), which is
  (13 + 4√3)/9. A new START clears the previous result; faults and aborted runs do
  not publish a fresh result.

## Limitations

- **Retirement is untagged.** The frozen core's retirement carries no execution id.
  An injected retirement while awaiting completion cannot be told from the real one
  (`research/h0_rtl_1f/COUNTEREXAMPLE.md`). R3 relies on reset coverage of the
  single retirement-producing hierarchy, supported by source inspection and
  simulation only.
- **Reset and clock** are a single-domain simulation expression, not a reviewed
  physical reset or CDC design.
- **Run identity** (`run_id`) wraps and resets on physical reset; freshness is tested
  within one session, not across resets.
- Fixed 14-instruction program shape; wrapper ends at PC 14 and does not use the
  frozen frontend's HALT state.
- No synthesis, timing or hardware results exist for H0.

## Direction (not implemented)

Keeping transport independence, validation, ownership and result association in a
small common control model could let other devices reuse the host-control concepts
with their own execution formats. This is a possibility, not a design or a claim.
