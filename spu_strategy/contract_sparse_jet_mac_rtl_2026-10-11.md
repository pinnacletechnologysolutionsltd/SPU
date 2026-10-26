# Sparse Jet MAC RTL implementation contract

```bash
python3 -B software/tests/test_sparse_jet_mac_oracle.py
TB_FILTER=spu13_jet python3 run_all_tests.py
```

Date: 2026-10-11. Status: COMPLETE — frozen standalone RTL simulation scope.
Authority: owner permits the RTL tranche under a separate contract including
shared-multiplier reset/drain. The owner subsequently approved one full qualification attempt: 7,200 seconds
wall-clock and cumulative, including the separate 25 MHz Padé gate. No
sparse-specific synthesis/mapping campaign budget is supplied.
Spec author: Codex. Implementer: halt-and-flag reviewer. Auditor: repository
gates and owner evidence review. These are functional roles, not delegated agents.

## Scope and baseline

Use the [qualified software contract](contract_sparse_jet_mac_oracle_2026-10-10.md),
[primitive specification](../docs/SPARSE_JET_MAC.md), and
[closure hashes](../build/sparse_jet_mac/qualification_01/qualification_review.json).
Implement only new `hardware/rtl/core/spu13/spu13_jet_sparse_mac.v` and, if
needed to keep each module within 150 lines, `spu13_jet_sparse_idx.v`.
Add `hardware/tests/spu13/spu13_jet_sparse_mac_tb.v`, its two test-only
`spu13_jet_sparse*_checks.vh` includes, the `sparse_jet_rtl_vectors.py` fixture
generator, and a focused software
oracle/RTL driver `software/tests/test_sparse_jet_mac_rtl.py`.
Generate fixtures through that driver into a new child of `build/sparse_jet_mac/`;
do not hand-edit golden words. Reuse the independent polynomial oracle.

Do not change dense MAC, multiplier, core dispatch, production arithmetic,
digon cost tables, ISA, transports, WF, Surd or REGEN. No board operation or
application performance claim is included. Integration into a multi-client
arbiter requires its own contract; the present harness grants exclusive use.

## Implement in this order

1. Review baseline source hashes and these invariants. Halt on an unhandled
   contradiction; record the counterexample and minimal correction.
2. Implement tags and the value-blind order-major index generator. Execution
   support is N=2 and N=4, coefficient lanes fixed at 32 bits. Preserve the
   N=15 five-bit tag boundary as a width-only elaboration/control check.
   Use `TAG_BITS=$clog2(N+2)`, widen tag sums to TAG_BITS+1, then clamp.
   Canonical empty is [N+1,0]. Tag union treats empty as identity. Trust valid
   tags in hardware; simulation monitors reject malformed tags, coefficients
   outside 0..p-1 and nonzero coefficients outside the declared window.
3. Match the dense module's coefficient-array and four-component multiplier
   buses, with added input/output tags; expose clk/rst_n/start/op_mul,
   busy/done and err_zero_divisor. Do not add unused WIDTH parametrization.
   Valid multiplication and addition always return err_zero_divisor=0,
   including zero divisors. No inverse or singularity detector is added.
4. Capture operands, tags and operation only on IDLE acceptance. Ignore starts
   while busy and on retirement. ISSUE launches one scheduled product;
   WAIT accepts exactly one response; RETIRE publishes result/tag atomically.
   Reset dominates all states. Hold prior result until retirement, then emit
   one-cycle done with busy low. Busy covers acceptance through retirement;
   no pre-completion gap. Empty and addition take at least one busy cycle.
5. Keep one outstanding multiply. Pulse mult_start once per pair, wait for
   mult_done before advancing, and ignore responses outside WAIT. Compute
   exact modular accumulation without runtime division/modulo or floating
   point. No value-dependent product skipping or tag sharpening is permitted.
6. Implement and test the fabric ownership rules below before testing reuse.
7. Compare RTL values, tags, flags and issue order/count with independent
   expectations; compare handshake invariants, not fixed latency, with the
   qualified software contract. Keep legacy dense arithmetic regression.

## Shared-multiplier reset/drain contract

The harness/issuer owns exclusive fabric access from acceptance until the last
response has been consumed and retirement finishes. It must not interleave
another client, and must not present a start while the fabric is unavailable.
Ordinary completion leaves no outstanding response.

For common reset, assert rst_n to both MAC and multiplier, clearing outstanding
valid stages before release; use the existing multiplier reset semantics.
Check busy=0 and no residual done before allowing the next start. Reset clears
MAC result/tag to zero/empty and suppresses retirement and mult_start.

If only the MAC resets, the owner must retain fabric ownership, block all new
starts, consume/discard any old response, and establish multiplier idle before
reuse. This drain lives in the harness/owner, not an invented MAC epoch port.
Do not accept new work merely because the reset MAC reports busy=0. Never
inject a stale untagged response into a new WAIT and claim the MAC can identify
it. Without common reset or proven drain, reset/reuse conformance must FAIL.

Tests must cover reset during ISSUE, WAIT and RETIRE, simultaneous reset/start/
response, delayed old responses after MAC-only reset, immediate following-edge
acceptance after valid completion, and reset release with the fabric unavailable.
The drain test must show old response disposal before the next request issues.
Inject premature reuse as a negative control and require the ownership monitor
to fail; also falsify early busy drop, duplicate done, missing/extra issue and
incorrect completion result/tag. Test both a variable-latency supplier and the
actual shared multiplier. Supplier timing may differ; arithmetic and ownership
must agree. Do not infer top-level arbitration correctness from this harness.

## Acceptance and qualification

All 305 N=2/N=4 ordered window pairs must pass arithmetic, conservative tag,
exact count and ordering checks. Cover dense, scalar, empty, annihilated,
all-zero but dense-tagged, cancellation, coefficient extrema, basis products,
nonzero zero divisors, aliases and source mutation after acceptance. Withhold
responses and require busy to remain high without fabricated completion.

After implementation, run the following gates on frozen sources. Long jobs
use `tools/run_detached_job.sh` with a new output child and an owner-frozen
attempt/timeout/cumulative budget; do not launch without that budget.

```bash
python3 software/tests/test_sparse_jet_mac_rtl.py
TB_FILTER=spu13_jet python3 run_all_tests.py
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
bash tools/verify_repo.sh
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

Focused driver PASS is recorded in `build/sparse_jet_mac/rtl_focused_05/`.
All 305 window pairs, 1,950 fixture executions across direct and delayed
responses, reset/drain controls and nine falsifiable negative controls passed.
N15 is a tag-width-only check. Full qualification_01 is COMPLETE, exit 0, in 2,072 seconds. All 14 gates
passed: repository 244/0, scoped 68/0, source checks and separate 25 MHz Padé.
[Closure record](../build/sparse_jet_mac/rtl_qualification_01/qualification_review.json)
records the gate exits and 2,050 tested source hashes.
The mandatory Padé build does not synthesize or qualify the sparse module;
any sparse-specific mapping/timing attempt needs its own configuration and
budget. Report software, RTL simulation, synthesis, routing, interface and
silicon evidence independently. Software and bounded standalone RTL simulation are qualified; core integration,
multi-client arbitration and sparse physical implementation are NOT RUN. Speedup, energy and board performance are unmeasured.
