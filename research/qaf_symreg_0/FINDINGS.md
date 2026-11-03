# QAF-SYMREG-0 — bounded software feasibility

**Recommendation: REVISE.** The model demonstrates sound reuse in the tested
cases, but this repeated-query fixture gives no advantage over a manually
hoisted baseline. Refine the workload and cost model before proposing an
architectural optimization. This is exploratory software, not an ISA change,
RTL result, simulator conformance claim or hardware performance result.

## Hypothesis and scope

Versioned, proven relationships between Q(√3) registers may allow a previously
computed algebraic norm to be reused without changing numerical results.
`model.py` maintains eight exact `(a,b,d)` registers, bounds, equality and
norm-equality facts, and norm caches. A successful write invalidates every fact
dependent on the overwritten version. Invalid loads and refused multiplies
preserve destination, version, facts and cache. Claimed equality, norm equality
and coefficient bounds are checked before admission; they are not trusted hints.
Conjugate values can have equal norms without being equal values.

The model imports `raw`, `valid` and `normalize` from the existing
`software/experiments/surd_register_exact.py` reference. For multiplication it
commits a fitting raw tuple unreduced, otherwise normalizes and refuses if the
result still does not fit. Tests use both W=8 and W=64. The relevant
[experimental Surd ISA description](../../knowledge/isa_reference.md) defines
signed 64-bit coefficients, a positive unsigned denominator, raw-fit commit and
destination preservation on failure. `SNORM` in that description is tuple
normalization; the algebraic norm queried here is a **software observation**,
not an existing hardware instruction. Other operations, status-register effects,
instruction encoding, timing and complete ISA conformance are outside scope.

## Reproduction

Run from the repository root; outputs go to the terminal. The source baseline
was `87833c7` with unrelated worktree changes present. Python 3.10.12 and Z3
4.15.5 from OSS CAD Suite 20261027 were used. Each invocation below has a
30-second wall limit and a 1 GiB per-process virtual-address limit. No random
input or seed is used; other tool paths may need adjustment.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_symreg_0.test_model -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_symreg_0.benchmark)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/qaf_symreg_0/bounded_equality.smt2)
```

## Results

Six test groups passed, including 196 small-domain tuples against an independent
`Fraction` identity `(a+b)(a-b)-2b²`, equality and conjugate norm relations,
invalid claims and bounds, stale fact invalidation, refusal preservation,
raw-fit non-normalization and overflow rescue. No correctness mismatches were
observed. The W=8 overflow example rejects `120 × 2` and retains the prior
destination and relationships. The explicitly false equality/norm claims and
understated bounds were rejected. These are finite tests, not a proof of the
whole model.

Z3 returned **`unsat`**, then **`sat`** for the negative control. The first is
a complete bit-vector check over the specified 4-bit signed coefficients and
nonzero 4-bit unsigned denominators: equal values cannot have unequal norms.
All intermediate arithmetic is widened to 32 bits, sufficient for this finite
domain. The second removes the equality premise and exhibits the fixed stale
relation `1` versus `2`. This establishes neither the Python implementation nor
64-bit architectural behavior, nor any property of overflow/refusal beyond the
stated formula. No timeout occurred.

The deterministic benchmark queries the norm of two differently encoded equal
values alternately 10,000 times. Each measured implementation's outputs matched
the independent oracle; the test process ran concurrently with the unit tests.
One observational run produced:

| Implementation | Norm evaluations | Reuses | Bookkeeping units | Proof multiplications | Time (s) | Peak Python bytes |
|---|---:|---:|---:|---:|---:|---:|
| Numerical, repeated | 10,000 | 0 | 0 | 0 | 0.028725 | 845,596 |
| Manual hoist | 1 | 9,999 | 0 | 0 | 0.000417 | 85,712 |
| Shadow facts | 1 | 9,999 | 10,007 | 4 | 0.009301 | 87,764 |

Each actual norm formula uses four integer multiplications and one subtraction;
the shadow case also performs four cross-products to establish value equality.
Direct norm-equality admission uses ten multiplications. Bookkeeping is the
model's explicit counter for selected version, lookup and invalidation actions,
not a hardware instruction count or a complete accounting of Python operations.
The manual baseline knows this fixed workload's equality in advance. Times are
single samples with interpreter, allocation and scheduling effects; peak
`tracemalloc` allocation includes the result list and is not metadata alone.
There is no statistical speed or energy claim. The avoided numerical operations
do not establish an architectural advantage; on this fixture the simpler
manual hoist is faster and has lower measured peak allocation.

## Limitations and next decision

The benchmark intentionally favors repeated queries and contains no mutations,
aliasing or refusals in the timed path. The model uses Python unbounded integers
for checking relations and `Fraction` for norms; proof costs, invalidation scans
and coefficient growth would need a realistic compiler/VM workload and a fair
optimized baseline. Bounds are verified observations, not static range analysis.
The solver's bounded equality lemma does not prove cache invalidation or the
imported arithmetic. Compare mixed writes, real instruction streams and full
metadata cost before any promotion; investigate whether an ordinary optimizer
already performs the same reuse. No hardware or release gate is proposed.
