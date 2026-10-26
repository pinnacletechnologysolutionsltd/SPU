# QCG-0 P0 implementation plan (planning material only; no code written)

Date: 2026-10-23. Author: Claude, under the owner's engineering handoff. Subject: contract Revision 3.2.1
(`1f8aca9f088ffbaafb002ba5cffde7bdee7b33fdfcf18dcf20dec16202b8cf2f`, independent PASS), decisions D-1…D-6 accepted. Scope of this
document: read-only inspection and planning. No candidate code exists or was created; no certified file, frozen contract or stage allowance was
touched; the reviewer's W31 derivation was not attempted. Freeze, implementation and P0 execution remain HOLD.

## 1. Reusable components (audit result)

**Nothing in the repository can be imported unchanged without altering a frozen algorithm, ledger rule or refusal semantics.** What exists
is reusable only as a pattern, and several contract rules are deliberately unlike the older code:

| Existing item | Path | Verdict |
|---|---|---|
| Checked rational with counters and atomic refusal | `research/qsg0/rational.py` (`Arithmetic`, `R`) | **Pattern only.** Fixed R32 bounds, integer-division counters, `Counter` keys differ from the contract's M/A/S/D/K/G/W categories, one gcd per op is only implicit, no raw sub-checks, no event ids. Write a fresh `Q` with profile-parameterized bounds. |
| Labeled operations with a stage trace; Horner, product, derivative | `research/qsg2/algebra.py` (`Field.op`, `horner`, `multiply`, `derivative`) | **Pattern only.** Labels (`label.i.mul`) are not the contract's event grammar; `multiply` zero-initializes and adds every term (contract: first term initializes). |
| Independent Fraction oracle: convolution, Horner, de Casteljau, derivative controls | `research/qsg2/oracle.py` | **Idea for O1/O2, not importable.** Cubic-specific (`3*`), a different campaign's frozen code; the contract requires O1 and O2 written fresh. |
| Synthetic-division Taylor shift | `software/lib/jet_ring_N.py::taylor_shift_N` | **Same loop as the contract's TSHIFT** (j outer, i descending to j) but over A31 jets; structural confirmation only. |
| Counters over a field | `software/lib/a31_field.py::OpCount`, `research/rel1/exact.py::Ops` | Pattern only; A31 is excluded from QCG-0 geometry. |
| Refusal classes (atomic bounded engine) | `research/fpra_1a/bounded.py::ArithLimit` | Pattern for exception-based atomic refusal. |
| Reference data loading | none needed beyond `json`, `hashlib` | Pinned JSON files are read directly (§3). |
| Forward differencing, power→Bernstein conversion, PCOMP | nowhere in the repository | Written fresh. |

Tests: `research/**` is outside `run_all_tests.py`'s gate; QCG-0 tests run directly (`python3 -B -I research/qcg_0/p0/test_p0.py`).

## 2. A constraint found while planning

`python3 -I` (isolated mode) does **not** put the script's directory on `sys.path`, so sibling imports (`import ledger`) fail under the contract's
command. Repo precedent is an explicit insertion (`research/rel1/exact.py`, `research/qsg2/run.py`). Plan: `run.py` and `test_p0.py` begin with
`sys.path.insert(0, str(Path(__file__).resolve().parent))` and nothing else; the pinned files make this auditable. No contract change is needed.

## 3. Layout (new, isolated; `research/qcg_0/p0/`; each file ≤ 150 lines)

The contract's file list is a minimum. Where a module would exceed 150 lines it is split; every file is listed in `PINS.sha256`.

| File | Responsibility | Depends on |
|---|---|---|
| `ledger.py` | `Q` (canonical rational; one gcd per M/A/D; literal-2/½ shifts; semantic K; W proxy; raw and reduced checks; per-op sub-check order), `Ledger` (categories, phase tags, additive/max aggregation, T/L tracking) | stdlib |
| `events.py` | route context, event-id construction, status grammar, `Refusal` exceptions, profile objects (P4096, W31) | ledger |
| `poly.py` | `HORNER`, `DECAS`, `TSHIFT`, `FDINIT`, `FDSTEP` exactly as §5 | ledger, events |
| `prep.py` | `PMUL`, `PADD`, `PSUB`, `PSCALE2`, `PDER`, `PINT`, `PCOMP`, `BERN`, declared-degree truncation; steps P1–P31 | poly, ledger |
| `refs.py` | load and hash-verify pinned JSON; field mapping (Cell A adapted pair, original doubled once, sequential pair derivation oracle-side, Cell B rows, P-1 supplemental, CH1/joins/loops) | json, hashlib |
| `arms_a.py` | Cell A arms: B-Horner, B-Bezier, B-TS, B-PH, C1, C2, B-FD (`NOT_APPLICABLE`); steps a1–a9, b1–b19, c1–c12 | prep, poly |
| `arms_b.py` | Cell B arms: B-COMP, C1 (h1–h13), E-COMP/E-BEZ/E-TS (k1–k8); P16–P31 | prep, poly |
| `arms_seq.py` | sequential arms and tapes S1–S3 with the required-step table, FD/TS/PHFD/C2 evolution, post-P snapshot | arms_a, poly |
| `joins.py` | S5/S6: chain CH1, gated join predicates, loops, retiming requests (`DIRECTION`, `TANGENT`, `CURVATURE`, length requests) | prep, ledger |
| `gates.py` | Pareto evaluation: comparator selection, guard G\*, trigger Tr, TRADE-OFF, equivalence EQ-1/EQ-2 | ledger |
| `o1.py`, `o2.py` | independent oracles (Fraction polynomial route; integer-pair/Bernstein/difference route), written without importing the arms | stdlib |
| `mutants.py` | X-1…X-24 harness; the W31 expectation hook reads the reviewer's certified JSON | arms, refs |
| `run.py` | single-invocation program in the contract's order; the bounded writer (running total, per-file size, `CAP_BREACH`, exit 90, `RUNNER_DONE` last); no SIGTERM/SIGXFSZ handler; exit codes 0/90/1–99, never 124 | all |
| `test_p0.py` | conformance rows LU-H…LU-G, LU-P, EQ-3 on Cell A, grammar/event tests | all |
| `launch.sh`, `PINS.sha256`, `TOOLS.manifest` | exactly as specified in contract §9; created **last** (hashes depend on the final files) | — |

Estimated size 1,600–1,900 lines across 17–20 files.

## 4. Interfaces

* **Arm:** `prepare(source, profile) -> state | PREPARATION_REFUSED(event)`; `request(state, request) -> (status, outputs)`. The source is the certified `(U, V, h=1, r_0=(0,0))` and, for Cell B, φ. Retained state lives in an immutable structure; a `snapshot()`/`restore()` pair supports the sequential tapes and the X-16 state-hash comparison (copies are not operations).
* **Request:** `{"cell": "A"|"B"|"S1"|"S2"|"S3"|"S4"|"S5"|"S6", "index": int, "param": [n, d], "kind": "BUNDLE"|"DIRECTION"|"TANGENT"|"CURVATURE"|"ORIENTED_LENGTH"|"ACCUMULATED_LENGTH"|"PIECEWISE_LENGTH"}`.
* **Result:** `{"status", "code", "event", "outputs": [[n,d],…], "ok_flag"}`; rationals are canonical `[numerator, positive denominator]` pairs.
* **Ledger JSON:** per arm: `{phase: {category: value}}` for P and Q, derived totals, `T_ret_peak`, `L_peak`, attempt ledger separately; deterministic key order.
* **Artifact:** versioned UTF-8 JSON with every arm's retained state, ledgers, outputs, statuses, event ids, the Pareto evaluation and mutant results; hashed and read back by an independent reader function.

## 5. Coding dependencies and order

1. **T0** `ledger.py`, `events.py`, `poly.py` and the LU rows (no arms yet): pure arithmetic, checkable against the contract's closed-form counts.
2. **T1** `prep.py`, `refs.py`, `arms_a.py`, `o1.py`/`o2.py`, EQ-3 on Cell A (28/27, 26/23 query counts; preparation 43/30/8/14, 31/22/5/14, 27/22/5/14), `gates.py`.
3. **T2** `arms_b.py`, `arms_seq.py` (Cell B hand counts 21/18 and 33/31; sequential tapes against `sequential`).
4. **T3** `joins.py`, `mutants.py` (X-1…X-24 with fixtures; the sequential/Cell B W31 rows wait for the certificate).
5. **T4** `run.py` (bounded writer, ordering, artifact write/readback), `test_p0.py` completion, then `launch.sh`, `TOOLS.manifest`, `PINS.sha256` last.

## 6. What remains blocked, and by what

| Item | Blocked by |
|---|---|
| Sequential and Cell B W31 first-refusal expectations (X-15 beyond Cell A) | the reviewer's stage-table certificate (authorized, not yet delivered); code can be written with a hook and the rows enabled when the certificate exists |
| Any candidate code | implementation authorization (HOLD) |
| `PINS.sha256`, `TOOLS.manifest`, `launch.sh` content, the frozen budget and command | contract freeze, which needs the final file list and the stage tables |
| Running P0, benchmarks, the launcher on a real run | separate execution authorization |
| Acceptance of results | independent review after execution |

Not blocked: reading references, writing this plan, and (once authorized) development work in T0–T4 with ordinary unit tests.

## 7. Smallest bounded implementation authorization that lets me begin

**"QCG-0 implementation block T0–T4, development only."** Scope: create and edit files **only** under `research/qcg_0/p0/` (and delete my own temporary
files); the Revision 3.2.1 contract and every pinned reference unchanged; run only development unit tests, each under
`/usr/bin/timeout 60 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304 -- /usr/bin/python3 -B -I …`, no network, no installs, no children,
no persistent output beyond `build/qcg_0/dev/`; a **stub-runner self-test of `launch.sh`** in a scratch leaf (it exercises the launcher's classification
and finalization paths without running P0); no use of the reviewer's allowance, no stage derivation; and **no execution of `run.py` as P0**.
End state: code complete, tests green, `PINS.sha256`/`TOOLS.manifest` drafted but not frozen, and a short report of any contract ambiguity found.
Anything the code reveals as ambiguous in the contract is reported to the owner before it is resolved; I do not choose an algorithm silently.

## 8. Risks I would watch (no action needed now)

* The contract's rules differ from common library behaviour in small places that would silently pass most tests: no zero skipping, one gcd per
  M/A/D even for integers, literal-only shifts, administrative checks uncounted, `bn(0)=1`, event counters spanning nested primitives. Each has a
  LU row; implement the rows before the arms.
* O1/O2 must not share helpers with the arms (a shared bug would pass EQ-3). They are written without importing `ledger`, `poly` or `prep`.
* The bounded writer must be the only path to disk (including logs) so the cap contract and `RUNNER_DONE`-last hold.
