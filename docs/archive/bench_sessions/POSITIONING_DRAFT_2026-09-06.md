# Positioning drafts — 2026-09-06

**Status: DRAFT, not a claim of record.** Two registers of the same idea:
§1 is the technical positioning statement (for the site, the typestate paper's
introduction, or a first outreach artifact); §2 is the plain-language on-ramp
for a reader who has never heard of an algebraic number field.

Every silicon citation below was checked against `docs/hardware_evidence.md`
on 2026-09-06. §3 records what these drafts deliberately do **not** claim, and
why — that section is load-bearing, not boilerplate.

---

## 1. Positioning statement

> **SPU is an exact rational coprocessor for computational geometry, closed
> rotation groups, and structural invariant checking.** It computes over closed
> algebraic number fields — $\mathbb{Q}(\sqrt3)$, $A_{31}$, $\mathbb{Z}[\varphi]$ —
> so that rotations compose without drift, orientation tests cannot flip sign,
> and an admissibility check either passes or refuses. In hardware, at fixed
> latency.

Floating-point geometry has a well-known failure mode: near collinearity, an
orientation determinant returns the wrong sign, and a point ends up both inside
and outside the same face. Meshes tear, CSG kernels crash, prints fail. Compose
rotation matrices for long enough and $RR^{T} \neq I$ — the transform stops
being a rotation, and lengths quietly stretch.

**This is not an unsolved problem, and the honest pitch says so.** Shewchuk's
adaptive-precision predicates (1997) and CGAL's exact-geometric-computation
kernel are what production CAD actually runs on, and they are fast precisely
because they escalate to higher precision only near degeneracy.

That escalation is the cost SPU removes. An adaptive predicate's runtime depends
on its input; SPU's does not. For a real-time controller, a safety case, or any
pipeline that has to be timing-deterministic, *"exact, and always the same number
of cycles"* is a different guarantee from *"exact, usually quickly."* That is the
claim — narrower than "nobody can do this," and it holds up under an
adversarial read.

The architecture earns this by staying inside its closure. A rotation drawn from
a finite group composes forever with no operand growth. A predicate is a bounded
algebraic evaluation. A guard is a static check. None of these accumulate error,
because none of them need to represent a quantity that grows.

### What is proven on silicon

| Capability | Evidence | Board, date |
|---|---|---|
| Closed rotation groups — period-6 orbit, exact root closure on phase 5, **early closure rejected** | §3.2h | Tang Primer 25K, 2026-07-01 |
| Structural invariant guard — 5 fixtures, 4 of them faults (topology, strut collision, collapsed cable, grid mismatch) | §3.2l | Wukong Artix-7, 2026-07-14 |
| Guard four-act completion, 10/10 runs, zero deviations | §3.2l.1 | Wukong Artix-7, 2026-08-09 |
| Exact unitary matrix arithmetic, standalone SU3 full oracle | §3.2e.6 | Wukong A7 100T, 2026-08-07 |
| Video → rasterized geometry → depth-resolved image | §3.8, §3.9, §3.10 | Wukong A7 100T, 2026-09-04/05/06 |

The guard entry is the one to lead with. Four of its five fixtures are faults,
so what is proven is that it **refuses** — an admission guard that only ever
accepts has demonstrated nothing.

---

## 2. Plain-language on-ramp: the valve body

Before the 1990s, an automatic transmission contained no electronics at all. It
still decided, correctly, thousands of times per trip, exactly when to change
gear. It did this with a machined aluminium casting called the *valve body* —
which the engineers who built it called the hydraulic brain.

It is a real computer, built out of oil:

| Electronics | Valve body |
|---|---|
| Wire | Milled channel |
| Resistor | Calibrated orifice |
| Capacitor | Accumulator piston and spring |
| Diode | Check ball |
| Comparator | Spool valve |

The comparison happens in steel. Governor pressure rises with road speed;
throttle pressure rises with engine load. The two push against opposite ends of
a spool, with a calibrated spring as the tiebreaker. When one side wins, the
spool moves — and here is the good part: the moment it starts moving, the fluid
reaches a different land area on the spool, so the force *jumps*. The valve
snaps rather than creeping. That is a Schmitt trigger with hysteresis, machined
out of metal, decades before anyone put one on a die.

**Why it is reliable is the whole point.** The invariants are enforced by
geometry rather than by convention. A check ball cannot pass fluid backwards on
an off day. A spool is open or closed — never 0.97 open. Nothing drifts, because
there is nothing for drift to accumulate in.

SPU applies that discipline to numbers instead of oil. A rotation either is an
element of the catalogue or does not exist; there is no "almost orthogonal."
A guard admits or refuses; there is no "probably in equilibrium." The arithmetic
lives in a closed algebraic field, so a value computed a million operations deep
is the value the mathematics specifies — not that value plus whatever the
rounding did on the way.

Floating point, by contrast, is a valve body whose bores wear a little on every
single shift. Usually it still finds the right gear. The engineering effort goes
into the *usually*.

**And the limit is worth stating,** because it is the same limit in both
machines. A transmission is a controller, not a computer: three or four states,
no memory, not programmable. Its power comes from the constraint. SPU is the
same trade — it is exact because its state stays inside a closed set, which is
precisely why it is the wrong tool for tracking a quantity that grows without
bound. **What it can compute is decided by what its catalogue can represent.**
That boundary is a live research question here, not a settled one.

---

## 3. What these drafts do not claim

Recorded so a later reader does not reintroduce the claims by accident.

1. **Not "pixel-perfect," and no crack-freedom result.** §3.10's own table
   records the depth boundary at **0.5058** (sd 0.0010, 24 scanlines) against
   **0.5000** predicted — 0.58% of screen width, ~3.7 px in 640, with two
   observations across a power cycle at 0.5062 and 0.4986. Shared-edge
   crack-freedom is **not tested anywhere**; it is a proposed demo, not
   evidence. Do not cite §3.9/§3.10 for it.
2. **Not a PDE solver, and the reason is specific.** Nonlinear time-stepping
   needs repeated rescaling of a growing quantity, and rescaling is rounding.
   The problem is representing growth, *not* iteration depth — long-horizon
   iteration inside a finite ring is exact and unbounded.
3. **The catalogue boundary is open.** `8f3922e` (2026-09-06) falsified
   coordinated group rotation over the 24 discrete octahedral rotations —
   1/24 balanced, that one being the identity, 0 genuinely new geometry, with a
   quadrance-preservation control. The useful half is the scope limit: Fuller's
   Jitterbug is *continuous*, and its intermediate states are generally not
   representable in the $\mathbb{Z}[\varphi]$ ABI at all. The obstacle may be
   the representation rather than the physics. Whether a richer exact catalogue
   contains a reachable balanced set is untested.
4. **Do not rewrite the SOM history.** SOM was shelved on 2026-09-03 as a
   priorities call, not a technical defeat; it had landed cross-vendor silicon
   at 150/150 exact and a 147/150 trained Iris baseline. The positioning does
   not need a failure story to make the arc look inevitable.
