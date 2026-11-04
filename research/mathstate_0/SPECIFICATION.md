# MATHSTATE-0 — deferred materialization

Registered before experiment execution: **a sufficient condition for safe
substitution will likely require proof that both eager and substituted paths
avoid refusal, together with proof that omitted intermediate metadata and state
updates are not architecturally observable.** This prediction is a candidate
sufficient condition, not a claim that it is necessary. The experiment should
identify cases where final-only observation and full architectural observation
differ. Synthetic fixture frequency cannot establish general prevalence.

## Selected reference and boundary

Use the explicit-denominator Surd bank in the frozen Gen-1 v0.2 core and the
existing dispatch-port testbench. Eight registers contain signed 64-bit a,b
and unsigned nonzero 64-bit d, representing (a+b√3)/d. SLI/SLD load six
32-bit slices; SRD reads a slice; SADD, SSUB and SMUL execute tuple operations;
SNORM normalizes a tuple (not field norm); SSTAT reads status. Register
initialization bits are reset low; operand invalidity returns status 1. Raw
arithmetic is used when it fits, otherwise a normalizer attempts exact rescue;
unrepresentable normalized results return status 2, invalid/normalizer faults
can return 1 or 3, invalid encoding returns 4. Successful arithmetic writes a
tuple and marks destination valid; refusal does not write it. SSTAT reads the
previous status, whereas other instructions update status. The datapath uses
130-bit signed numerators and 128-bit unsigned denominators; alignment and
normalization have their own checks. See `hardware/rtl/core/spu13/` Surd
modules and the frozen `cpu_v02/rtl/spu13_core.v`.

Architectural readback of a register or status between instructions can expose
intermediate state; the frozen demonstration frontend itself admits only its
restricted program profile. Dispatch-port testing therefore establishes
selected core behavior, not arbitrary frontend program behavior. The Surd bank
has initialization validity and status but no identified enabled Eager
Coherency metadata interface: **EAGER_COHERENCY_METADATA = UNKNOWN / NOT
ESTABLISHED IN GEN-1**. No software Pell metadata is attributed to RTL.

The exact generator u=2+√3 acts on (a,b) by [[2,3],[1,2]] and inverse
[[2,-3],[-1,2]]. EAGER executes the software reference one instruction at a
time; FUSED composes matrices; GENERATOR retains an exponent; CERTIFIED allows
replacement only on a proven per-fixture sufficient condition. Exact algebra,
machine-representable tuple operations, and state equivalence are distinct.
Final-only comparisons cannot establish agreement when intermediate state can
be observed. Reports must distinguish unavailable or unproven properties from
false ones. RTL test evidence is limited to the executed traces.
