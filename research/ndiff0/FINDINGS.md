# NDIFF-0 — Native differentiation through PH representation: initial software probe

2026-10-25. Host-only, stdlib Python, exact arithmetic. No RTL, ISA, simulator, SIM-CAP1 or shared-gate change.
Status: **software-only, single author, no independent acceptance.** Not added to `run_all_tests.py`.

```bash
python3 -I -B research/ndiff0/test_ndiff0.py   # controls
python3 -I -B research/ndiff0/run.py           # Phase 2: correctness + costs
python3 -I -B research/ndiff0/phase3.py        # Phase 3: closure
python3 -I -B research/ndiff0/phase4.py        # Phase 4: Eisenstein (exploratory)
python3 -I -B research/ndiff0/scaling.py       # structural counts vs degree
.venv/bin/python -I -B research/ndiff0/sympy_check.py   # OPTIONAL SymPy cross-check; pip install -r research/ndiff0/requirements-research.txt
```

## Phase 1 discrepancies (reported before use)

| Brief assumed | Found |
|---|---|
| SymPy oracle | Not in system Python; later found in `.venv` (SymPy 1.14.0, gitignored) and used for `sympy_check.py`. The core probe's oracle is stdlib Fractions with a **binomial Taylor-shift** (independent of the k·c_k derivative rule). Same author, so source-separation only. |
| Jet code over Q(√3) | `software/lib/jet_ring.py` is J = **A₃₁**[ε]/ε³, not Q(√3): not reusable. Dual/jet Horner was rewritten over Q(√3). |
| QSG-2 reusable | QSG-2 is **Q only**, linear generators, and already found the *ordinary factored* baseline faster than its PH candidate (`docs/QSG2_SOFTWARE_RESULTS.md`). Not reused; not contradicted (see below). |
| QCG-0 | Algebraic-curve/quintic fixtures, not PH. Not used. |
| H2 hex/Pell | Reused as background only: hex lattice embeds in Q(√3) Cartesian; Pell scalings leave the lattice. |

## Phase 2 — Euclidean PH over Q(√3)

Curve: generators a,b of degree 2 with surd/rational coefficients → hodograph degree 4, position degree 5.
Cost model frozen in `field.py` (surd mul = 4mR+2aR+1kR). Gate frozen in `cost.gate`.

* Correctness: 210 exact comparisons (3 strategies × 6 points incl. surd t₀ × orders 1,2) against the oracle.
* Denominators introduced by integration: X {1,3,24,54,80}, Y {1,2,3,18,20,24}. Generators 3-bit → hodograph 7-bit → position 7/7-bit (num/den). Bounded here; not a worst-case claim.
* Construction (shared by every strategy): 42 surd mul. Baseline additionally needs derivative polynomials (10 kmul); PH stores a,b instead.
* Repeated evaluation, order 1 (P, P′, |P′|², |P|², d|P|²/dt), rational ops (mR/aR):

| | PH | poly Horner | jet Horner |
|---|---:|---:|---:|
| surd mul / add | 22 / 18 | 24 / 21 | 24 / 21 |
| mR / aR | 88 / 80 | 96 / 90 | 96 / 90 |
| order 2 (adds P″) mR / aR | 112 / 100 | 120 / 114 | 120 / 114 |

**Frozen gate: ADVANTAGE (structural count), small.** Savings come only from the tangent/speed² part
(generator degree d: PH 2d+3 muls vs 4d for Horner on the hodograph): saving = 2d−2 surd muls (d=1 tie; d=2: 2;
d=6: 10; `scaling.py`). Position evaluation (the dominant cost) is identical. Not wall-clock: no timing was taken.
Exact speed σ is a PH-only *output* (baselines have no exact √); it is excluded from the gate.
This does not contradict QSG-2: its baseline was already PH-aware ("ordinary factored"), which equals the PH column here.

## Phase 3 — closure (decided by exact computation, not by a failed construction)

Three notions: (1) PH property in Q(√3) (psqrt finds σ′ ∈ Q(√3)[t]); (2) primitive generators h=1; (3) generalised h·(a,b)
with real polynomial h. For (2), unique factorisation reduces closure to "does a constant √u exist in K(i)".

| Transform | PH property | primitive h=1 | generalised (h,a,b) |
|---|---|---|---|
| rotate 0/60/120/180° | yes | yes | yes |
| rotate **30°, 90°** | yes | **no** (needs cos15°∈√6,√2; √2) | **yes** (z=1+i·tan(θ/2), h′=h/(1+t²)) |
| scale 3, 7+4√3, 1/4 | yes | yes | yes |
| scale **√3**, 2, 2+√3 | yes (σ′=λσ) | **no** (3^¼, √2, √(2+√3)) | **yes** (h′=λh) |
| t→t² | yes (σ′=2t·σ(t²)) | **no** (h=2t, odd valuation) | **yes** (h′=2t·h(t²)) |

So √3 scaling does **not** admit primitive generators in Q(√3) (they need 3^¼) while the PH property and the
generalised form stay in-domain. Caveats: t→t² makes P′(0)=0 (σ(0)=0, regularity lost) and the speed identity is
σ′=2tσ(t²) only for t≥0. The generalised form costs more: evaluating the t² curve: PH 40 vs 44 surd mul (curve degree
doubles; h adds 3 muls + a Horner). t→1/t not attempted (optional; poles undefined here).

## Phase 4 — Eisenstein (exploratory)

N(a+bω)=a²−ab+b² is the Euclidean quadrance in oblique coordinates (verified on 81 lattice points against the
Cartesian image), so the PH identity N(ζ²)=N(ζ)² transfers **unchanged** — it is not a new metric. (The a²+ab+b²
convention is the same norm in the e^{iπ/3} basis; the wrong-sign form is rejected by a control.) Generators in Q(ω)
give a different curve class (x∈Q[t], y∈√3·Q[t]) with a **rational** speed polynomial h·N(ζ). Cross-checked at 4
points against the Cartesian Q(√3) route. Cost within Q(ω), schoolbook E·E = 4mR+3aR, rational t₀:
PH 30 mR / 24 aR vs poly Horner 28 mR / 25 aR — **no advantage** there (derivative Horner at rational t₀ is cheap).
Different class from Phase 2, so absolute counts (30 vs 88 mR) are not a PH comparison.

## SymPy cross-check (`sympy_check.py`, SymPy 1.14.0)

Independent symbolic route (sympy integrate/diff/expand over Q(√3)), same generator numbers: positions, hodograph,
speed identity x′²+y′²=σ², and 288 strategy outputs (3 strategies × 6 points × orders 1,2) all match the candidate.
Closure facts: the constants needed for primitive generators have degree 2 over Q(√3) (cos15°, √2, 3^¼, √(2+√3):
outside), controls √3 and cos30° have degree 1 (inside). The 30° generalised form (tan15°=2−√3) and the t→t² form
are verified symbolically. Not fully independent of me (same author, same curve); the Fraction oracle and SymPy
agree with each other, which is the stronger evidence. Pinned in `requirements-research.txt`; the stdlib probe is the mandatory test, SymPy is optional.

## Recommendation: **NARROW**

* Exact polynomial speed/arc length is real; the evaluation saving is 2 of 24 surd muls (5 of 45 mul+add, ~11%) at d=2 and 19 of 109 mul+add (~19%) at d=6, but only on the tangent/speed² slice and only for curves already in PH form.
* The honest architectural finding is Phase 3: PH closure under similarities depends on *which representation is
  stored*; only the generalised (h,a,b) form is closed in Q(√3), at extra cost. A native-ISA case would have to be
  made on exact-speed/arc-length outputs, not on cost.
* Not demonstrated: wall-clock speed, worst-case coefficient growth, composition of multiple transforms, jets of
  speed itself, anything on hardware. Stop condition: if a future wall-clock or composed-transform test shows no
  gain, STOP; otherwise a narrowed follow-up is "generalised-form (h,a,b) cost under composed similarities".
