# Engineering Contract: Padé service-state oracle PSS-1

**Date:** 2026-10-12  
**Status:** DRAFT — source audit and software experiment specification; not qualified  
**Contract ID:** `contract_pade_service_state_pss1_2026-10-12.md`

Roles: Codex drafts and reviews; an implementation pass follows lifecycle review;
repository gates audit any subsequent implementation. No additional agent is
required. The active Artix-7 job, AOR, GCR-1 and closed tranches remain independent.

## 1. Commands and authority

Run these documentation-only checks now:

```bash
python3 tools/doc_audit.py --actual-pass 243
git diff --check -- spu_strategy/contract_pade_service_state_pss1_2026-10-12.md docs/PADE_SERVICE_STATE_PSS1_REVIEW_2026-10-12.md docs/README.md
```

243 is the retained verified suite count in the decoder campaign's
`regression_02/repository.stdout.log`, not a new regression result.

After lifecycle ratification, the proposed software files and exact focused
command are:

```bash
python3 software/tests/test_pade_service_state_pss1.py
```

That command is not executable yet. Do not launch qualification from this draft.
No RTL edits, hardware job, synthesis, timing campaign or shared-runner changes
are authorized here. The user's instruction starts this tranche's preparation.
The existing three-attempt Artix-7 allocation cannot fund this tranche.

## 2. Target and exclusions

Model the service protocol of
[the A31 evaluator](../hardware/rtl/gpu/rplu_thimble_pade.v), fixed at
`NUM_COEFF=5`, `COEFF_ADDR_W=3`, `PADE_DEBUG_TRACE=0`, separately for
`PADE_PIPELINED=0` and `1`. Do not conflate it with
[the Q32/Q16 evaluator](../hardware/rtl/gpu/pade_eval_4_4.v).

Initial new files, after review:

- `software/lib/pade_service_state_pss1.py`: bounded reference event model.
- `software/tests/pade_service_state_pss1_oracle.py`: independent obligations checker.
- `software/tests/test_pade_service_state_pss1.py`: literal traces and mutations.

Keep each concern in a small module; split fixtures when necessary. No imports
of production arithmetic kernels or copying the RTL FSM into the checker.
The checker uses request/response ownership and ordered phase obligations.
Software agreement alone establishes neither RTL execution nor integration.

CPU retirement, SPI packet behavior, sidecar lane addressing, shared-arbiter
implementation, RNS error pipelines, mathematical Padé accuracy, GPU depth,
Surd, REGEN, AOR and physical timing are outside initial acceptance.
Existing arithmetic fixtures may supply named payloads with hashes; their
reuse is not fresh arithmetic qualification.

## 3. Pre-execution discrepancy and disposition

[STATE_MACHINE_HARNESS §3.4](../docs/STATE_MACHINE_HARNESS.md) describes held
DONE/SINGULAR states, explicit consumption/clear and zero output on singularity.
Those are a proposed abstraction, not this evaluator's current interface.
Actual source returns to IDLE and pulses `done` on both outcomes. Singularity
sets `flags_v` and leaves result registers untouched. There is no acknowledgement
or explicit-clear input. The declared `S_DONE` encoding is unused.

Do not implement the older held-state description or modify RTL to make it true.
Ratify the source-faithful lifecycle below before implementing the model. The
[AGENTS contract](../AGENTS.md) requires: “HALT immediately and flag the flaw”.
This draft is the minimal correction to the experiment specification.

## 4. Proposed source-faithful lifecycle

| Event | Required observation | Source boundary |
|---|---|---|
| Reset asserted | IDLE; busy, done, flags_v, mult_start and inv_start cleared; no commit | Evaluator reset block, lines 235–245 |
| Start sampled in IDLE | Admit one evaluation, clear flags_v, assert busy and request numerator multiply | lines 250–272 |
| Start sampled while active | No second admission; no queued request | start examined only in IDLE |
| Numerator Horner | Four accepted multiply results, ordered from coefficient 3 through 0 | lines 276–318 |
| Denominator Horner | Four accepted multiply results; then inverter request | lines 319–350 |
| Inverter awaiting acceptance | inv_start can repeat until inv_busy acknowledges | lines 354–358 |
| Unit inversion completion | Issue final numerator × inverse multiply | lines 359–382 |
| Final multiply completion | Write all four results, done=1, busy=0, return IDLE | lines 387–395 |
| Singular inversion completion | flags_v=1, done=1, busy=0, return IDLE; no result write | lines 359–366 |
| Next non-reset edge | done returns to zero; flags_v holds until next admission/reset | lines 246–255 |

A successful evaluation needs nine multiply transactions: four numerator,
four denominator, one final. A singular evaluation needs eight and no final
multiply. Count accepted transactions, not repeated inverter start assertions.
Completion and idle occur together; do not require busy to remain asserted on
the completion edge or invent a result-consumption transition.

Result contents before first success are unspecified, including after reset.
After a known success, a singularity or reset preserves the result bits because
reset does not assign them. A preserved value is not a new valid completion.
Reset aborts the active evaluation; it does not retire it as a fault.

## 5. Owner obligations and supported input domain

- Four limbs of each supplied A31 operand/coefficient are canonical residues
  `0 <= limb < 2**31-1`; coefficient addresses are 0–4.
- Program coefficients with no active evaluation; leave all coefficients and
  saddle inputs stable from admission through completion or reset. Saddle is
  read again during Horner and is not fully snapshotted at admission.
- Coefficient storage is initialized at elaboration, not reloaded by evaluator
  reset. Its write process is independent of reset and busy. This profile
  forbids coefficient writes during reset or active evaluation; it cannot claim
  the RTL rejects them. Reset/reload are distinct operations.
- Pulse start for one edge; a held start can re-admit after completion. A pulse
  while busy is ignored rather than queued. Test these as distinct behaviors.
- Provide a multiplier able to accept every emitted request. `mult_busy` is not
  consulted by this evaluator. There is no multiplier backpressure contract.
- Provide inv_busy acceptance followed by one inv_done response; repeated
  inv_start before acknowledgement is one pending transaction.
- Return exactly one matching response for each accepted request, with stable
  payload at the sampling edge and no same-edge zero-latency response.
- The owner must reset or drain outstanding engines before reusing the service
  after reset. No stale response may cross into a new transaction.

Ownership IDs and reset epochs are checker metadata, not tags in the RTL.
An untagged stale response can be indistinguishable from a legitimate response.
The checker can reject an externally labelled violation; do not claim that the
current evaluator itself detects it. Invalid addresses, noncanonical limbs,
concurrent reconfiguration, engine refusal and unsolicited responses are
UNSUPPORTED stimulus domains, not newly allocated hardware faults.

The pipelined profile registers multiplier result/done for one additional
handoff edge, with that register reset independently. Compare ordered results
and transaction counts across profiles; latency vectors remain separate.

## 6. Observation and independent oracle

Each trace frame records cycle; pre-edge input signals and four-limb payloads;
post-edge start/busy/done/flags/result signals; externally assigned transaction
and engine owner IDs; reset epoch; accepted requests; response consumptions;
and result-write events. The driver must specify pre-edge drive and post-edge
sampling to avoid nonblocking-assignment races. A pure software model must
publish the same edge convention; it must not label a synthetic trace as RTL.

The obligations checker independently tracks:

1. At most one admitted evaluation; start while active does not create ownership.
2. Eight ordered Horner responses preceding inversion; final multiply only on unit outcome.
3. Each consumed engine response belongs to its outstanding request and reset epoch.
4. Exactly one completion per successful/singular admitted evaluation, and none for aborted evaluations.
5. Four-limb atomic result write only on successful final response; known previous result survives singularity/abort.
6. Completion pulse and held flags behavior; clean recovery via a fresh start.
7. Direct versus registered multiplier handoff and reset clearing of pending handoff.

Use literal expected admission/completion/write counts and hand-authored boundary
traces, independent of the model's private state names. Missing mandatory fields
are UNVERIFIED; they must never become PASS. Record MATCHING, CONFLICTING,
UNSUPPORTED and UNVERIFIED independently from suite PASS/FAIL.
A31 is a split algebra: singular inputs include nonzero zero divisors. Do not
restrict the inverter fault scenario to the all-zero denominator.

## 7. Required cases and negative controls

Positive cases: unit success; zero and nonzero-singular denominator outcomes;
success → singular → success with poisoned previous output; ignored busy-start;
held-start re-admission; minimum and delayed engine completions; repeated
inverter request until busy; asynchronous reset in numerator, denominator,
inversion before/after acceptance, final multiply, registered handoff and at
completion; owner reset/drain followed by a fresh evaluation; coefficient
persistence across reset. Cover both PADE_PIPELINED profiles separately.

Negative controls mutate an independently accepted trace to introduce:

- Completion before required responses.
- Duplicate completion or transaction admission.
- Stale response owner/reset epoch.
- Wrong phase consuming a response.
- Result write on singularity or abort.
- Partial tuple write or changed preserved destination.
- Final multiply after singular inversion.
- Inverted/cleared singular status before fresh start/reset.
- Missing mandatory ownership or observation fields.
- Registered handoff consumed on the direct-profile edge.

Every mutation must be detected for its declared reason. A checker accepting a
known invalid trace is a qualification failure. Unsupported environmental
stimulus being classified correctly is a positive classification test, not an
RTL mismatch or demonstrated hardware fault detector.

## 8. Bounded execution and promotion

Before execution, freeze the enumerated trace list, source/tool hashes, profile,
seed (if generated cases are added), maximum cycles per trace, number of traces,
exact command, timeout and evidence directory. No unbounded random testing.
Proposed first software experiment: one attempt, 900 seconds maximum and
cumulative; budget NOT AUTHORIZED by this draft. Wall-clock limit is an external
watchdog, never a service fault code. No automatic retries.

Any work expected to exceed 60 seconds must use `tools/run_detached_job.sh`
with a new `build/pade_service_state_pss1/<unique-id>` output, explicit timeout
and desktop notification. Record LAUNCHED then end the agent turn. Interpret
only a unique COMPLETE/FAILED/TIMEOUT marker. Preserve counterexamples and
before/after source hashes; timeout is neither functional PASS nor FAIL.

After software review, propose an observation-only RTL testbench with controlled
engine responders and actual-cycle trace capture. Do not change production RTL
or integration to fit the model. A detected valid-domain mismatch requires a
separate reviewed minimal repair. Testbench/oracle changes retain the full
AGENTS §4 gates before closure, including a separately budgeted 25 MHz Padé
build; serialize FPGA tools behind the existing CPU campaign. Do not substitute
that Padé build for integrated CPU timing or consume the CPU attempt budget.

Close initial software scope only with independent checker rejection evidence,
matched source hashes, explicit supported-domain table and recorded gate
results. RTL execution, integration, synthesis, silicon and performance remain
NOT RUN until independently established.
