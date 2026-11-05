# H0 overview: experimental host-control layer for the Gen-1 Surd CPU

**Status: experimental.** The R3 controller described below has simulation
evidence; a later UART-equipped H0 image has separate implementation-tool and
single-session board evidence ([ledger §3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc)). Neither establishes design qualification. H0 is the
control layer between a host and the execution hardware: load a program, validate
it, start one execution, and read results, without the host managing instruction
fetch, handshakes or reset sequencing. Experimental evidence and the full list of
limitations: [`research/h0_rtl_1f_r3/INTEGRATION.md`](../research/h0_rtl_1f_r3/INTEGRATION.md).

## Pieces and their evidence

| Piece | What exists | Evidence |
|---|---|---|
| Software model | `software/spu_host/h0_program.py`: load / verify / execute / result for one restricted 14-instruction program shape; `docs/H0_SW_2_PROGRAM_INTERFACE.md` | 5 unit tests in the release regression |
| RTL controller | `research/h0_rtl_1f_r3/`: two program banks, START ownership, reset sequencing, frontend, frozen Gen-1 core | RTL simulation: `run_focused.py`, 4 negative controls, independent arithmetic oracle |
| Transport | Experimental UART path and board package; SPI not established here | UART RTL simulation and one board session, separately described in [§3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc) |

The software model and the RTL controller are separate. They expose different
operations (the model: load/verify/execute/result; the RTL: bank write,
validate/promote, START) and have **not** been checked against each other.

## Behaviour demonstrated in RTL simulation

- **Two banks.** Each holds 14 words of 64 bits (R3 storage). This is distinct from
  the frozen frontend's fixed 16-word ROM, which R3 does not modify or reuse. A candidate is written to the
  inactive bank and promoted only after a scan of the fixed instruction shape (six SLI,
  SLD, SMUL, six SRD) and a CRC-32 comparison against the expected value; a failed replacement leaves the previous program intact. CRC-32
  detects accidental corruption only. It is not authentication.
- **Single owner.** An accepted START reserves ownership; competing START, load and
  promotion requests are refused until completion. A rejected START that stays high
  is not replayed later (negative control `replayed_start`). Non-preemptive.
- **Reset without losing the program.** START holds the execution domain in reset
  for at least two sampled clock edges, releases it synchronously, and enables
  fetch/issue only after initialization and core boot. The verified bank is kept.
  Two different programs (A, B) ran in sequence in simulation without any
  reconfiguration in the R3 simulation. The later UART-equipped board image ran
  two programs without recorded intervening reconfiguration ([§3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc)).
- **Results.** Six 32-bit slices, e.g. program A gives (13, 0, 4, 0, 9, 0), which is
  (13 + 4√3)/9. A new START clears the previous result; faults and aborted runs do
  not publish a fresh result.

## Limitations

- **Retirement is untagged.** The frozen core's retirement carries no execution id.
  An injected retirement while awaiting completion cannot be told from the real one
  (`research/h0_rtl_1f/COUNTEREXAMPLE.md`). R3 relies on reset coverage of the
  single retirement-producing hierarchy. This holds only if the clock and reset are
  shared and reliable, nothing else drives retirement, and no new issue is accepted
  during the reset flush; it is supported by source inspection and simulation, not
  proven or physically qualified.
- **Reset and clock:** R3's simulation is not itself a physical reset or CDC
  qualification. The later board image's tool-reported reset and timing checks
  and their limitations are recorded separately in §3.46.
- **Run identity** (`run_id`) wraps and resets on physical reset; freshness is tested
  within one session, not across resets.
- Fixed 14-instruction program shape; wrapper ends at PC 14 and does not use the
  frozen frontend's HALT state.
- SPI transport and physical qualification remain open. The later UART image was
  synthesized, routed and observed on one board; tool timing estimates are not
  measured timing margins, and the single session does not qualify the interface.
