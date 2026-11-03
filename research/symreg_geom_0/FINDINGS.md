# SYMREG-GEOM-0 findings

**PASS — BOUNDED DISCOVERY.** A symbolic producer composed identity and
quarter-turn matrices without reading vector coefficients. An independent
checker, using a separate versioned certificate, recomputed the composition and
checked MᵀM=I. For matrices it accepts, this identity entails Q(Mv)=Q(v) for
all vectors over Q(sqrt(3)), by exact ring algebra. The checker does not trust
a preservation label or import the producer. The certificate is a proof of a
matrix property; it does not assert that any physical execution used it.

Six focused test groups passed. They cover quarter-turn chains of zero through
eight steps, 625 exact rational-coefficient vectors using an independent
`Fraction` oracle, forged compositions, malformed and oversized input, Boolean
matrix entries and resource exhaustion. The incorrect transform (2x,y) was
rejected universally, even though the concrete vector x=0 makes its quadrance
unchanged; x=1,y=0 supplies a concrete counterexample. Concrete verification
and universal structural verification are different claims.

## Solver record

Z3 4.15.5 checked [verification.smt2](verification.smt2), QF_BV, with four
signed 4-bit coefficients sign-extended to 16 bits before products. It asks
whether either exact coefficient of Q changes after the quarter-turn: UNSAT.
The deliberately incorrect (2x,y) transform has a SAT counterexample with
coefficients (7,0,0,0). The widened range is sufficient for these bounded
expressions. This check is bounded and does not verify Python implementation,
arbitrary precision arithmetic, or ISA behavior. The independent matrix
identity provides the mathematical universal argument, conditional on the
checker correctly implementing its stated rules.

## Cost and limits

One illustrative eight-step certificate was 240 bytes. Thirty checks on
Python 3.10.12 had median 0.000146 s; traced peak allocation for one check was
7,261 bytes. These observations include parsing and do not imply hardware
performance. Setup and concrete vector arithmetic are excluded from the timing.

The only form is x²+y². The certificate supports bounded integer 2×2 matrices,
not general quadratic-field matrix entries, arbitrary symbolic expressions or
general geometric reasoning. The verified invariant is conditional on applying
the stated matrix to a vector; there is no vector identity, execution, context
authentication or freshness mechanism. SYMREG-5's authority-restart replay
counterexample remains unresolved. No ISA, RTL, FPGA or v0.2 qualification
claim follows. Bounds and encodings are specified in [SPECIFICATION.md](SPECIFICATION.md).

## Reproduction

Baseline `27185c3`; experiment remains untracked. Each local command has a
30-second external time limit and 1-GiB process address-space limit. No random
seed is used.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.symreg_geom_0.test_geom -v)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/symreg_geom_0/verification.smt2)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.symreg_geom_0.measure)
```

Expected solver results are UNSAT, then SAT with a counterexample. A standalone
checker is available as `python3 -m research.symreg_geom_0.checker CERTIFICATE`.
