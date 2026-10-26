# SPU research identity and maturity vocabulary

Adopted: 2026-10-19. This is the shared public description for the website,
README, research manuscripts and development roadmap.

> SPU is an experimental computing architecture exploring how exact algebraic
> arithmetic, geometric representations and deterministic transformations can
> support useful native computational primitives.

SPU pursues architectural invention grounded in existing mathematics. Its open
research and engineering work separates mathematical foundations, independent
verification, software architecture, hardware realization and exploratory
extensions. See [component licensing](../LICENSING.md) for reuse terms.
Original combinations and implementations are research aims; mathematical
novelty requires its own literature comparison and evidence.

The central research ambition is to investigate computational models in which
algebraic and geometric relationships are native state: what objects a machine
retains, which transformations it admits, and which observations it materializes.
This includes changes to execution and information movement, alongside arithmetic
primitives. A representation can change the trade-offs of a problem without
removing finite storage, expression growth or mathematical computability limits.
Conventional machines can implement these models; architectural benefit remains
a separate question from expressibility and mathematical correctness.

The [QSG-3 relational geometry model](QSG3_GEOMETRIC_MACHINE_SPECIFICATION.md)
proposes a first bounded investigation. Its initial milestone is composable,
invariant-preserving state transitions with explicit failures and observations.
Wall-clock speed is one later comparison, rather than the sole criterion for
deciding whether the computational model merits investigation.

> Architectural invention is the ambition; demonstrated utility is the test.
>
> Mathematical elegance motivates experiments; independent evidence determines
> architectural adoption.

## Maturity describes a scoped claim

| Level | Meaning |
|---|---|
| **Demonstrated** | Correctness and defined behavior verified within stated limits |
| **Experimental** | Implemented and testable, but comparative utility or hardware qualification remains unresolved |
| **Exploratory** | Mathematical or architectural hypothesis awaiting implementation and evidence |

Apply these terms to a named result, implementation or proposal, rather than
giving the entire project a qualification badge. The same component can have
demonstrated software correctness within a finite fixture, remain experimental
as an architectural primitive and have exploratory future hardware extensions.
Demonstrated correctness does not by itself establish comparative utility.

Pair a maturity label with its scope, arithmetic domain, bounds, source/artifact
identity, date, evidence and unresolved questions. State separately whether the
evidence is mathematical, software, RTL simulation, implementation-tool output
or physical observation. Preserve the stricter hardware claim rules in the
[evidence ledger](hardware_evidence.md). A tool estimate is not a qualified
physical measurement. A software result does not promote a hardware claim.

This vocabulary complements PASS, FAIL, HOLD, NOT RUN and contract acceptance
counts. Those record particular checks or decisions; the maturity terms do not
replace them or automatically advance any gate. Dated historical records retain
their original evidence boundaries; label current summaries explicitly.

## Utility has several possible dimensions

Speed is one possible benefit. A proposed primitive may instead provide
stronger determinism, exact invariant preservation, simpler verification,
lower energy use or lower total system complexity. Each needs an appropriate
conventional baseline and its own evidence.

| Proposed benefit | Comparison needed |
|---|---|
| Speed | Matched outputs, correctness requirements, workload and platform; include conversion and validation costs |
| Determinism | A defined repeatability or reproducibility guarantee, tested across the claimed runs, builds or devices |
| Exact invariant preservation | Independent exact checks and failure cases, compared with conventional exact arithmetic or robust methods where applicable |
| Simpler verification | Equivalent properties and coverage; measured proof/checking work and trusted assumptions |
| Lower energy | Qualified energy acquisition over matched complete tasks, with measurement uncertainty and platform stated |
| Lower total complexity | Explicit accounting of state, interfaces, conversions, verification and implementation costs across equivalent systems |

Report useful guarantees and their costs together. A gain in one dimension
does not establish gains in the others. Include refusal rates and bounded
coverage; rejecting difficult inputs can change what two systems actually do.

## Preserve negative results and integration hypotheses

The [QSG-0 rectangle experiment](QSG0_SOFTWARE_RESULTS.md) reports exact agreement
with its independent software oracle and the specified refusal behavior within
its tested scope. Its representation remains experimental: no architectural
advantage over conventional rational parameterization was established.
Its 0/5 research acceptance count remains pending independent result review.

A primitive with no established standalone advantage might help a larger
architecture. Record that as an exploratory integration hypothesis, preserve
the negative standalone result, and test the combined system against an
appropriate complete-system baseline before claiming a benefit. Possible future
integration does not discount present costs or justify hardware adoption.

## Apply the identity without expanding commitments

The [simulator integration policy](SIMULATOR_INTEGRATION_POLICY.md) makes the
simulator the cumulative software reference for qualified architectural
behavior. Research interpreters remain a testing ground; integration requires
qualified semantics and profile-specific simulator conformance. Software/RTL
functional qualification and physical FPGA qualification remain separate.

Finish a small, useful and reproducible Gen 1 machine and make its tools
accessible. Keep research tracks independently qualified and bounded. Admit
new representations or native operations only through their reviewed evidence
and existing implementation contracts. This public identity authorizes no
experiment, ISA change, RTL work, hardware budget or release claim.
