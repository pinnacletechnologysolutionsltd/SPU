# Scoping Note: Higher-`sigma_det` Operating Point for Pair-0 Calibration

**Date:** 2026-08-24
**Status:** SCOPED AND EVALUATED. **Not recommended for authorization
as originally framed.** No Monte Carlo/noisy simulation was run to
produce this note — only deterministic noiseless `m0_1` trajectories
(20,000 draws, no RNG noise machinery touched) and closed-form
evaluation of the already-fitted marginal law. This stays within the
"scope, don't experiment" bound John set for this whole follow-on.

**Directive:** per the pair-0 calibration contract's Phase 0 closure
(`contract_photonics_pair0_calibration_2026-08-24.md` §4) and John's own
framing of the next decision — "determine whether the higher-`sigma_det`
experiment has enough discriminatory power to justify authorization,
rather than automatically running it" — evaluate the idea before
proposing it as an actual Phase-1 design.

## 1. Why plain Monte Carlo at `sigma_det=3e-5` is impractical for pair 0

`m0_1`'s noiseless distribution (20,000 draws, deterministic, no noise
model needed): overwhelmingly `m0_1=8` (93.2%), with `m0_1=7` (6.4%) and
smaller tails at 5–6. The fitted marginal law
(`p_event_fit(m0, sigma_det)`, design-rule doc §1) predicts, averaged
over this distribution, `P(R_1=False) ≈ 0.075%` at `sigma_det=3e-5` —
implying `~267,000` trials needed for `n_min=200` failures, roughly
consistent with the Phase 0 run's own cost (~9 min for 300,000 trials,
so this alone would be tractable). **But the Phase 0 run's actual
observation — `0/300,000` — is not consistent with that rate.** At the
law's predicted rate, the expected failure count over 300,000 trials is
`~225`; the probability of observing exactly zero if that rate were
correct is `exp(-225) ≈ 3×10⁻⁹⁸`. **This is not sampling bad luck — the
fitted marginal law is decisively wrong about `R_1`'s true failure rate
at this specific position**, consistent with (an unusually stark
instance of) this whole campaign's already-documented magnitude-
conservatism bias (design-rule doc §4). **Practical consequence: any
`sigma_det` chosen by inverting the fitted law to hit a target failure
rate cannot be trusted without an empirical search** (matching E18's own
Gate-0 discipline) — the true required `sigma_det` could be
substantially different from what the law's inversion suggests, in
either direction.

## 2. A more serious problem, found while scoping: `sigma_det` is not
## per-event-tunable in this simulator — the "raise it for pair 0" idea
## has no valid path back into the existing estimator

`sigma_det` is a single, shared physical parameter applied to *every*
REGEN readout within one simulated trial/chain
(`run_chain_boundary_noisy_m0trace(pb, block, boundaries, sigma_det,
rng)` — one `sigma_det` argument for the whole 8-group chain, not one
per event). The corrected-reliability-model's whole-chain estimator
(`corrected_p_chain`) evaluates every trial at one fixed `sigma_det`
(currently `3e-5`, matching E18's calibration for pairs 1–6). **A
pair-0 calibration gathered at a *different*, higher `sigma_det`
(chosen specifically to make `R_1=False` observable) would characterize
`P(R_2=True|R_1,m0_2)` under that different noise regime — not under
`sigma_det=3e-5`.** Substituting it into the existing, `sigma_det=3e-5`
estimator would silently mix calibration data from two different
physical operating points into one product, with **no established
result showing this pairwise-conditional structure is `sigma_det`-
invariant** (the only invariance this campaign has established is
`M`-invariance — REGEN period — not `sigma_det`-invariance; design-rule
doc §1). This is not a minor caveat — **it disqualifies the simple
"raise `sigma_det`, calibrate pair 0, plug the number back in" design
outright**, independent of §1's cost/reliability concerns.

## 3. What would actually be valid, and why neither is worth authorizing now

Two paths avoid §2's coherence problem; both are materially bigger than
the original "just run more/hotter trials" framing implied:

- **(a) Rare-event techniques at the correct `sigma_det=3e-5`**
  (importance sampling, splitting, or another variance-reduction method
  that reweights biased draws back to the true physics). Valid in
  principle — stays at the right operating point — but is new,
  nontrivial simulation machinery for this codebase (nothing in
  `photonics/` currently does biased/reweighted sampling), with its own
  real risk of a subtle reweighting bug, and would need its own
  from-scratch validation before trusting any output. Not a small
  addition to the existing driver.
- **(b) Redo the *entire* E18-style calibration and corrected-model
  validation at one new, shared, higher `sigma_det`** (all 7 pairs, not
  just pair 0). Internally coherent (no mixed operating points), but
  this stops being "a pair-0 fix" — it's a parallel research question
  ("does the same viable-but-rejected-correction finding replicate at a
  different noise level?"), materially larger in scope (effectively
  re-running E18 + the corrected-reliability-model contract from
  scratch), and **does not repair the currently-rejected estimator at
  `sigma_det=3e-5`**, which is the actual open question. Not proposed.

## 4. Verdict

**The higher-`sigma_det` idea, as it was informally sketched
(`photonics-research-branch` memory, corrected-reliability-model
contract), does not survive scoping and is not recommended for
authorization.** Its central appeal — "just run trials where the rare
event isn't rare" — turns out to produce data that cannot be validly
substituted into the estimator it was meant to fix (§2), independent of
whether the rate/cost picture (§1) would have worked out. The two paths
that *would* be methodologically valid (§3) are each larger, riskier
undertakings than the original framing implied, and (b) doesn't even
answer the question it would be run to answer.

**This is itself the correct scoping outcome, not a stalled
investigation** — exactly analogous to Phase 0 potentially having come
back "not viable": the point of scoping before proposing is that a
design can fail at the scoping stage, and that's supposed to happen
sometimes. **Recommendation: do not add a higher-`sigma_det` Phase 1 to
the authorization queue.** If pair-0 calibration is ever pursued for a
real engineering reason (still none exists — the adopted
`predicted_p_chain` estimator doesn't need it), §3(a) is the only
methodologically sound path, and it should be scoped and Halt-and-Flag
reviewed as its own, larger piece of work — not assumed to be a cheap
follow-on to Phase 0.

## References

- `contract_photonics_pair0_calibration_2026-08-24.md` §3/§4 — the
  original (a)/(b) rare-event-vs-binning framing this note refines, and
  the Phase 0 result (`R_1` `n_false=0/300,000`) this note explains.
- `docs/PHOTONIC_REGEN_PLACEMENT_DESIGN_RULE.md` §1 — the fitted law and
  its already-documented conservatism, §1's `sigma_det=3e-5` prediction
  vs. observation discrepancy is a sharper instance of the same issue.
- `software/tests/run_photonic_m0_dynamic_range_sweep.py`,
  `run_chain_boundary_noisy_m0trace` — confirms `sigma_det` is a single
  chain-wide argument, the basis for §2's finding.
