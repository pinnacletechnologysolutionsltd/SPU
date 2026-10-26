# Sparse Jet MAC contract and software-oracle review

Date: 2026-10-10. Status: five corrections applied; focused software checks PASS; full frozen software qualification COMPLETE (reviewed 2026-10-11);
RTL implementation requires its separate contract. Authority: owner instruction to proceed through
contract and software-oracle review only.

## Findings resolved in the corrected contract

| Concern | Pre-correction source and counterexample | Applied correction |
|---|---|---|
| Arithmetic domain | [Existing contract](SPARSE_JET_MAC.md#2-what-it-computes) names F_(p^4). A31 has nonzero zero divisors; the checked example u=(s,0,0,1), v=(s,0,0,p-1), s²=15 mod p, has uv=0. | Specify A31[eps]/(eps^(N+1)), with A31 the split biquadratic algebra. Multiplication is defined for nonunits; inverse requires a unit constant coefficient. Correct field/local-ring descriptions without changing arithmetic. |
| Empty-tag width | [Interface](SPARSE_JET_MAC.md#4-interface-and-integration) says four bits suffice through N=15, but canonical empty lo=N+1=16 truncates to zero. | TAG_BITS=ceil(log2(N+2)); five bits at N=15. Compute tag sums with one extra bit before clamping. Initially review N=2 and N=4; N=15 is a width boundary control, not qualified RTL. |
| MAC fault semantics | [Dense source](../hardware/rtl/core/spu13/spu13_jet_mac.v) resets/clears err_zero_divisor and never asserts it. The proposed multiplicative-identity fault path does not exist. | Preserve actual dense multiplication/addition flag behavior: no new singularity fault for a valid product. Keep inverse rejection separate. Do not claim MAC unit detection or allocate a new flag. |
| Cost lower-bound claim | [Cost model](../software/lib/digon_recursive.py) charges p+2 for c0-chain steps and v1+1 for scalar products. At N=4, [1,4]×[1,4] issues six products versus the model's three; [0,0]×[1,4] issues four versus two. | Use exact window-intersection counts for the proposed primitive. Withdraw the claim that exact scheduling necessarily meets/beats every old modeled term. Audit workload totals separately before changing performance claims or the existing model. |
| Completion compatibility | Dense busy excludes ST_DONE: there is a phase with busy=0 before done pulses. The proposed completion-coupled contract cannot be attributed to this dense source. | Freeze sparse acceptance/completion/reset semantics separately. Compare dense values and actual flags; do not claim identical busy/done timing. Timing remains unverified by software. |

Per the root halt-and-flag contract, no sparse implementation is derived from
the inconsistent legacy text. These are explicit proposed corrections rather
than a silent RTL redesign. Existing dense RTL and arithmetic libraries remain
unchanged.

## Existing software-oracle evidence

[Review checks](../build/sparse_jet_mac/contract_review_01/review_checks.json)
bind the inspected source hashes and counterexamples. The fixed N=2 oracle
and general-N oracle agree on the nonzero-zero-divisor product. Base norm and
inverse rejection agree with the split-algebra interpretation. Independent
index enumeration confirms the N=2 reference counts 6/3/1 and the two N=4
cost counterexamples above. The empty-sentinel overflow is explicit.

This is a small contract review, not exhaustive arithmetic qualification,
a sparse oracle PASS, an RTL regression or a timing/resource result.

## Proposed software oracle slice

1. Freeze N=2 and N=4, canonical residues 0..p-1 in each of four 32-bit
   coefficient lanes, valid windows 0<=lo<=hi<=N and canonical empty [N+1,0].
   Reject other tags in the software monitor; trusted hardware tag provenance
   remains a sequencer responsibility rather than a value-based hardware scan.
2. Build an independent polynomial-basis A31 multiplication oracle using
   basis exponents and x²=3, y²=5. Compare both existing jet implementations
   at N=2 and the general oracle at N=4. Do not use shared a31_mul as the sole
   independent arithmetic expectation.
3. Enumerate all 305 ordered window pairs across N=2 and N=4, including empty
   and annihilated products. Compare order-major sparse schedules with an
   independently enumerated rectangular index set and the exact count formula.
4. Exercise canonical residue extrema, basis products, cancellation, nonzero
   zero divisors and deterministic random conforming jets. Assert exact dense
   coefficient agreement and conservative output windows. Do not sharpen tags
   when an in-window value happens to vanish.
5. Prove schedule/count independence from operand values. Include a deliberately
   mistagged nonzero channel, a missing scheduled product and an incorrect
   count as falsifiable negative controls. Treat value mismatch and unsupported
   input contracts separately.
6. Report operation counts and proposed handshake model checks only. The
   software contract now specifies acceptance, retirement and reset ownership;
   RTL latency, controller provenance, hardware cost and integration remain
   unverified. No RTL is authorized by passing software checks.

## Review deliverables

The [command-first contract](../spu_strategy/contract_sparse_jet_mac_oracle_2026-10-10.md)
and [corrected primitive contract](SPARSE_JET_MAC.md) resolve all five issues.
[Focused report](../build/sparse_jet_mac/oracle_preparation_01/focused_report_04.json):
646 arithmetic cases, 305 window pairs, 1,838 protocol traces, 24 negative
controls and five boundary controls passed. Hashes bind the software fixtures.
The independent oracle uses exponent-basis products and rectangular index
enumeration. Existing digon cost tables and production arithmetic/RTL are unchanged.

Completion tests cover variable latency, withheld responses, busy-time starts,
retirement-edge rejection, following-edge acceptance, operand capture, reset
cancellation and one-cycle completion. Shared reset/drain ownership is required;
an untagged stale response during a new WAIT remains outside the guarantee.
These model checks do not establish dense or sparse RTL timing conformance.

Full qualification completed in 2,169/7,200 seconds, exit 0, with exactly
one COMPLETE marker. All 13 gates passed: repository 243/0, scoped 67/0,
trace/math checks, independent oracle, source checks and the separate 25 MHz
Padé build. [Closure record](../build/sparse_jet_mac/qualification_01/qualification_review.json)
records gate exits and all 2,041 tested source hashes. The software tranche is
closed within this frozen scope; sparse RTL and fabric integration are unverified.
Proceed under the [separate implementation contract](../spu_strategy/contract_sparse_jet_mac_rtl_2026-10-11.md).
Integrated Surd/REGEN routing and timing acceptance remain independent.
