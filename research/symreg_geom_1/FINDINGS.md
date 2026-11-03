# SYMREG-GEOM-1 — findings

**PASS — BOUNDED DISCOVERY.** A version-2 symbolic certificate represents a
symmetric integer form G and a sequence of bounded integer matrices. The
independent checker reconstructs their composition M and checks every entry
of MᵀGM=G without examining a vector. For any accepted certificate, ordinary
exact matrix algebra entails Q_G(Mv)=Q_G(v) for all vectors over Q(sqrt(3)).
This mathematical consequence is conditional on the checker correctly
implementing its specified rules and on the stated transformation being used.

Five focused test groups passed. An independent rational-coefficient oracle
checked 625 vectors for each of four form/transformation pairs (2,500 checks):

* Euclidean G=diag(1,1), quarter-turn.
* Indefinite G=diag(1,-1), sign reflection.
* Cross-term G=[[2,1],[1,2]], transformation [[0,-1],[1,1]].
* Indefinite G=diag(1,-2), Pell-type transformation [[3,4],[2,3]].

The checker accepted selected compositions and a degenerate zero form. The
latter illustrates why preservation alone does not imply a distance or
positive-definite geometry. Controls reject the Euclidean quarter-turn for the
cross-term form, the cross-term transformation for the Euclidean form, forged
composition, nonsymmetric form, malformed/version-mismatched certificates and
resource overflows. Scaling (2x,y) is rejected as a universal Euclidean
invariant even though it agrees on the particular case x=0.

## Solver record

Z3 4.15.5 checked [verification.smt2](verification.smt2), QF_NIA. For
integer x,y and Q(x,y)=2x²+2xy+2y², a counterexample to preservation by
(-y,x+y) is UNSAT; the incorrect (-y,x) has a bounded SAT counterexample
(-1,-1). The first formula is an integer algebra check, not a solver proof of
the Python code or of all Q(sqrt(3)) inputs. The general-domain conclusion
comes from the checked matrix identity and ring algebra. Solver timeout was
25 seconds, external timeout 30 seconds, address-space limit 1 GiB.

## Cost and scope

An eight-step certificate measured 248 bytes. On Python 3.10.12, 30 checks
had a 0.000201 s median and one check used 7,304 bytes peak traced Python
allocation. Timing includes parsing and checking but excludes setup and
concrete vector arithmetic; it implies no hardware performance or advantage.

Only symmetric 2×2 integer forms and bounded 2×2 integer transformations
are implemented. Rational or quadratic-field matrix entries, higher dimensions
and general symbolic expressions are not supported. The certificate proves a
matrix property, not that a vector was actually transformed, and it provides
no context authentication or restart freshness. SYMREG-5's replay
counterexample remains. There is no ISA, RTL, FPGA or v0.2 qualification claim.

## Reproduction

Baseline `778be1c`; this experiment is separate and untracked. Commands use
30-second external and 1-GiB address-space limits; no random seed is used.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.symreg_geom_1.test_geom -v)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/symreg_geom_1/verification.smt2)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.symreg_geom_1.measure)
```

Expected solver outcomes: UNSAT, then SAT with a counterexample. The
standalone checker is `python3 -m research.symreg_geom_1.checker CERTIFICATE`.
