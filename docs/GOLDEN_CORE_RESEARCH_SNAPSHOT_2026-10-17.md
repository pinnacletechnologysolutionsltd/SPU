# Golden Core research snapshot

**As of:** 2026-10-17
**Scope:** Bounded exact software work GC-2A through GC-6
**Architecture:** No ISA, RTL, or hardware qualification

This snapshot collects the questions, finite results, evidence, limitations, and
reproduction paths from the Golden Core work. A PASS is limited to the exact
profile and fixtures named in its result record. GC-2A remains proposed and
unratified; later software results do not ratify the research contract or
support physical claims.

## Research sequence

| Stage | Question and result | Limits and evidence |
|---|---|---|
| **GC-2A — controlled chirality** | Bounded H1/H2 qualification accepted for review. Independent Python `Fraction` and C++ `cpp_int` arithmetic streams matched on 10,140 inputs. Covariance passed on the three declared substrate pairs, including fixtures without an admissible orientation-preserving identification. | Sampled arithmetic and finite fixtures, not universal proofs. GC-2A remains **PROPOSED / NOT RATIFIED**. Review: [`GC2A_BOUNDED_QUALIFICATION_REVIEW_20261016.md`](../build/gc2a_qualification/GC2A_BOUNDED_QUALIFICATION_REVIEW_20261016.md). Run records and corrected interpretation remain under `build/gc2a_qualification/`. The original frozen commands used local `/tmp/gc2a_qualification_20261016_v2/run_frozen_bundle.sh` and `/tmp/gc2a_h2_completion_20261016/run_frozen_h2.sh`; these are not clean-checkout commands. |
| **GC-2B — weighted geometry** | The finite 4-cycle `Q(√3)` fixture passed its declared exact covariance, internal-symmetry, trajectory, and negative-control checks. | This is a separate small substrate from the later icosahedron. Reproduce with `python3 software/tests/test_gc2b_weighted_covariance.py --manifest software/tests/fixtures/gc2b_weighted_cycle.json --report /tmp/gc2b_report.json`. Detached report: [`report.json`](../build/gc2b_qualification/20261016_run01/report.json). |
| **GC-3 — exact golden geometry** | A `Q(√5)` oracle and independent `Q(φ)` comparisons support one exact icosahedron, its incidence, equal edge quadrance, and a proper order-three rotation. | Does not establish all golden geometry. See [GC-3 report](GOLDEN_CORE_GC3_2026-10-16.md) and fixture [`golden_core_gc3_icosahedron.json`](../fixtures/golden_core_gc3_icosahedron.json). |
| **GC-4 — symmetry classification** | The frozen unlabelled icosahedron has 60 proper and 60 orientation-reversing spatial symmetries. One distinguished vertex leaves 10; unique vertex labels leave the identity. | Finite model only; unlabelled shape is achiral. See [GC-4 report](GOLDEN_CORE_GC4_2026-10-16.md) and fixture [`golden_core_gc4_icosahedral_symmetries.json`](../fixtures/golden_core_gc4_icosahedral_symmetries.json). |
| **GC-5 — oriented edge operator** | Exact left/right turn permutations on the 60 directed edges satisfy proper-map preservation and mirror exchange across all 120 spatial maps. | The unequal profile is signed linear arithmetic, not probabilities. It has 60 internal symmetries among the 120 tested spatial maps; this is not a classification of all linear symmetries. See [GC-5 specification](GOLDEN_CORE_GC5_ORIENTED_EDGE_OPERATOR_2026-10-17.md), [results](GOLDEN_CORE_GC5_RESULTS_2026-10-17.md), and fixture [`golden_core_gc5_oriented_edge_turns.json`](../fixtures/golden_core_gc5_oriented_edge_turns.json). |
| **GC-5A — first trajectory** | One impulse seed evolved exactly for 12 updates under neutral and signed laws. Mirror covariance held for all 120 maps at all 13 states. | One seed and finite horizon. See [GC-5A results](GOLDEN_CORE_GC5A_DYNAMICS_RESULTS_2026-10-17.md) and fixture [`golden_core_gc5a_edge_dynamics.json`](../fixtures/golden_core_gc5a_edge_dynamics.json). |
| **GC-5B — seed controls** | Four seeds × two profiles passed exact measurement and mirror-transport checks for 12 updates under one frozen reflection. Uniform remained a zero-defect control; other seed-relative observables differed. | No recurrence appeared only within steps 0–12; maximum coefficient size was 32 bits in these runs. See [GC-5B results](GOLDEN_CORE_GC5B_SEED_CONTROLS_RESULTS_2026-10-17.md) and fixture [`golden_core_gc5b_seed_controls.json`](../fixtures/golden_core_gc5b_seed_controls.json). |
| **GC-6 — reversibility** | Both existing 60D operators have exact rank 60 and zero nullity over `Q(√5)`; two-sided inverses pass. The separate paired-state rule and its inverse pass on all 120 basis states and mirror covariance passes for all 120 frozen maps. | Paired state changes the dynamics. Reversibility does not define a Janus point. See [GC-6 results](GOLDEN_CORE_GC6_REVERSIBILITY_RESULTS_2026-10-17.md), [specification](GOLDEN_CORE_GC6_REVERSIBILITY_SPEC_2026-10-17.md), and fixture [`golden_core_gc6_reversibility.json`](../fixtures/golden_core_gc6_reversibility.json). |

## Reproduction commands

Run from the repository root with Python 3.10+:

```bash
python3 software/tests/test_gc2b_weighted_covariance.py --manifest software/tests/fixtures/gc2b_weighted_cycle.json --report /tmp/gc2b_report.json
python3 software/tests/test_golden_core_gc3.py
python3 software/tests/test_icosahedral_catalog.py
python3 software/tests/test_golden_core_gc4.py
python3 software/tests/test_golden_core_gc5.py
python3 software/tests/test_golden_core_gc5a.py
python3 software/tests/test_golden_core_gc5b.py
python3 software/tests/test_golden_core_gc6.py
```

GC-2A's outcome is preserved as dated detached-run evidence. Its H1/H2 source
bundle currently resides in local `/tmp` directories, so the original
qualification is **not reproducible from a clean checkout** using the commands
above. Do not treat the report link as a replacement for those sources.

## Interpretation boundaries

- Algebraic conjugation, spatial parity, substrate chirality, law-level bias,
  and an asymmetric state are distinct constructions.
- Covariance relates an experiment to its transported mirror. It does not
  imply an internal symmetry on the original substrate.
- The GC-5/GC-6 operators are linear transformations on a finite exact vector
  space. The GC-5B parity-defect count is a nonlinear state comparison against
  one chosen reflection.
- The finite runs establish no physical chirality, cosmological relation,
  long-term dynamical property, speedup, energy advantage, or hardware fit.
- The signed weights include a negative coefficient and are not transition
  probabilities.

The associated [Quadray and golden-geometry demonstrations](SUPPORTED_DEMOS.md#quadray-to-golden-core)
separate browser rendering, Python exact computation, and the optional T1d
software simulator.
