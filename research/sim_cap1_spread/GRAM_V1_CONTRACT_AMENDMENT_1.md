# gram_v1 SPREAD — Contract Amendment 1 (2026-10-25)

Amends `GRAM_V1_CONTRACT_FROZEN.md` (left unedited). Owner-approved in the SIM-CAP1 integration
authorization. Software-only. Staging/commit remains HOLD (see §8).

## 1. Width bound (replaces the loose "2^72 / 2^148" figures; those remain valid upper bounds)
With |lane| <= M = 2^31 (INT32_MIN included): lane product p<=2^64, q<=2^63; 4*dot p<=2^68,
q<=2^67; (sum v)(sum w) p<=2^68, q<=2^67; **B: p<=2^69, q<=2^68**; D = Bvv*Bww: p<1.75*2^138<2^139,
q<=2^138; Bvw^2 likewise; **|N| < 2^140** (N = D - Bvw^2). Signed 256-bit range is +-2^255, so
no intermediate wraps and truncation cannot alter an exact result (>=115 bits of headroom).
Empirical check (read-only review): 85,536 cases (all 2^16 INT32_MIN/INT32_MAX lane assignments plus
20,000 random) matched an unbounded oracle exactly; observed maxima 68 bits (B), 137 bits (D, N).

## 2. Degeneracy proof (p-lane)
B(v,v) = sum_{i<j}(v_i - v_j)^2. With v_i - v_j = x + y*sqrt3, the square's p-part is x^2 + 3y^2 >= 0,
so the p-lane of B(v,v) is a sum of non-negative integers and is zero iff every difference has
x = y = 0, i.e. all four components are equal. B(v,v) = (0,0) is therefore equivalent to that
condition, and the exact (p,q) pair zero test is a complete degeneracy test.

## 3. Scale dependence of OVERFLOW
Scaling both operands by lambda scales (N, D) by lambda^4 (B is bilinear, N and D are degree 4).
Representability of the *unreduced* result is therefore scale-dependent: a reduced form may fit
int32 where the unreduced one does not. This follows from the unreduced-output decision and is
intended; OVERFLOW is defined on the unreduced (N, D) and nothing else.

## 4. Mandatory tests (separate classes)
* **Pell cancellation witness (mandatory, stands alone):** u=(708158977,408855776),
  w=(708158977,-408855776), a=(3u,0,0,0), b=(3w,0,0,0) plus the lane-shifted and sign variants in
  the suites. Inputs fit int32, B itself exceeds int32, result MUST commit N=(0,0), D=(729,0).
* **Boundary pairs:** just-fits/just-overflows (c=124/125 on D.p; surd lane c=71/72).
* **Corner/random sweep:** supports implementation correctness; it does not replace the witness.

## 5. Manifest placement (amends contract section 2)
The spread entry is at top level `metric_semantics_detail.spread_opcode_0x15`, in the same entry
shape as a capability, beside the `metric_semantics` field. The existing `capabilities` schema and
its validation (`test_cpu_profile.py`: each listed test id is `file::name` with `name` in that file)
are unchanged. Moving the entry into `capabilities` would be a separate schema decision.

## 6. Proof output (amends section 2; Python and C++ now agree)
Under `gram_v1`, `--proof` prints, in both VMs, the line
`B(v,v)=(p,q) B(w,w)=(p,q) B(v,w)=(p,q)` (decimal coefficients) before the result line. Legacy
proof output is unchanged. C++ B values fit __int128 (each coefficient < 2^70).

## 7. Atomicity definition (amends section 4)
A refused SPREAD changes nothing except `halted`/`fault_kind`: registers, QR registers (and
typestate tags), call stack, snap counter, PC, step count, log. Verified for both fault kinds,
for rd=10 and for the rd=25 -> R0 wrap, in Python (full attribute comparison) and C++ (full-state
dump of 26 scalars, 13 QRs, call stack, snap counter, PC, steps).

## 8. Integration status
Suites: `software/tests/test_gram_v1_spread.py`, `test_gram_v1_spread_cpp.py`; shared oracle
`software/tests/gram_v1_oracle.py`; registered in `run_all_tests.py` (explicit Python list).
HOLD: staging/commit (mixed working tree; `checked_math.h` ownership; `software/vm/spu_vm` binary
stays unstaged); `doc_audit --actual-pass` update (needs the actual count from a full run, not
authorized); SIM-GRAM-1 for the separate `spu-sim` (separate frozen gate).
