# Exact Geometric Computation Primer

Date: 2026-09-18  
Status: **PARKED - research primer only**  
Owner: SPU research track

This document describes a research programme, not an implementation contract.
It authorizes no RTL, ISA allocation, training run, model download, synthesis,
formal campaign, or hardware work. Any execution requires a separate
owner-authorized contract with frozen inputs, commands, limits, and stop
conditions.

## 1. Purpose

This programme explores whether useful computation can be expressed through
exact geometric and algebraic operations rather than primarily through
approximate floating-point matrix arithmetic.

The working principle is:

> Treat geometry as computation.

Candidate operations include reflections, lattice translations, discrete
transport, loop invariants, and deterministic gates. Established mathematics,
proposed architecture, and experimental results must remain explicitly
separate.

## 2. Basic computational model

```text
state -> exact transform -> exact observation -> gate/routing -> next state
```

State may use integer or lattice coordinates, finite-ring elements, exact
surds, discrete group elements, or bounded algebraic residues where practical.
The objective is not to eliminate approximation from training, but to make
execution deterministic and reproducible.

## 3. Weyl and Coxeter operations

Finite `E8` has eight simple generators:

```text
s_1, ..., s_8
```

A transformation can be represented by a finite word:

```text
w = s_i1 s_i2 ... s_iL
```

The proposed computational interpretation is:

```text
generator = instruction
Weyl word = program
common word = macro or intrinsic
```

This is a parameterization and execution choice. Weyl transformations also
have matrix representations; the proposal is to execute constrained generator
operations rather than store unrestricted dense matrices.

### 3.1 Arithmetic-circuit selection

The E8 label does not by itself determine the arithmetic cost. A generic dense
`8 x 8` matrix-vector product should not be the default implementation model
for a simple Weyl reflection. For a root `alpha` with the conventional
normalization `(alpha, alpha) = 2`,

```text
s_alpha(x) = x - (x, alpha) alpha
```

The first optimization question is therefore whether the chosen coordinates
reduce the reflection to permutations, sign changes, additions/subtractions,
and simple constant scaling. The intended optimization order is:

```text
Weyl/root structure
    -> sparse and shift/add circuit
    -> common-subexpression elimination
    -> bilinear reduction for products that remain
```

Karatsuba is relevant to the last step, not to E8 dimensionality itself. For
an exact quadratic-surds value `x = a + b sqrt(3)` and
`y = c + d sqrt(3)`, the direct product uses four scalar products. The
three-product form is:

```text
p0 = a*c
p1 = b*d
p2 = (a+b)*(c+d)

xy = (p0 + 3*p1) + (p2 - p0 - p1) sqrt(3)
```

This trades one variable multiplication for additions and recombination. The
same question can be asked of affine E8 translations and any exact scaling
arithmetic, but the affine generator must still be derived as an exact
reflection before translations are treated as compiled macros.

This is a research hypothesis, not an RTL choice. Each candidate primitive
must compare a straightforward circuit, a structure-exploiting circuit, and a
Karatsuba/bilinear variant for exactness, LUTs, DSP use, latency, and timing.
The preferred result may be that suitable coordinates make Karatsuba
unnecessary for most Weyl generators.

## 4. Finite, affine, and hyperbolic progression

The research path is:

```text
E8 -> E8^(1) -> E10
```

It should be described as:

```text
finite -> affine/translational -> hyperbolic
```

not as a simple increase in Euclidean dimension.

### Stage 1: finite E8

Initial goals are to implement the eight simple reflections exactly, verify
Coxeter relations, preserve lattice membership and invariants, and test whether
useful learned behaviour survives compilation into a short exact word.

Arithmetic optimization is subordinate to this gate: first derive the exact
root action and its coordinate-level circuit, then measure whether any genuine
variable-by-variable products remain worth reducing.

### Stage 2: affine E8^(1)

The primitive instruction set becomes:

```text
s_0, s_1, ..., s_8
```

The ninth generator is an affine reflection, not merely a translation opcode.
Translations arise through compositions of affine reflections and may be
represented as compiled macro-words.

A scaled lattice may be defined as:

```text
Lambda_N = (1/N) Lambda_E8
```

Hardware can retain integer coordinates `X` and interpret state as `x = X/N`,
keeping division outside the execution hot path.

### Stage 3: hyperbolic E10

`E10` supplies a hyperbolic Coxeter structure with ten simple generators. Its
possible uses in hierarchical routing, structured sequence traversal, symbolic
navigation, and high-capacity discrete routing remain hypotheses.

Any fixed-width implementation must explicitly define a finite quotient,
coordinate bound, or other exact finite encoding for unbounded mathematical
state.

## 5. Exact arithmetic and finite quotients

A candidate arithmetic hierarchy is:

```text
Z/pZ <- Z/p^2Z <- Z/p^3Z <- ...
```

Each finite `k` gives an exact computational representation. This is related to
`p`-adic mathematics but is not the same as storing the infinite ring `Z_p` in
hardware.

Reduction modulo `p^k` preserves selected algebraic identities exactly; it
does not automatically reproduce the geometry or representation theory of a
corresponding real Lie group. The defensible claim is that finite quotient
arithmetic provides an exact algebraic execution model whose preserved
properties must be established explicitly.

## 6. Discrete holonomy

Assign exact transport operators to edges of a graph or lattice. For a path
`gamma = e_1 e_2 ... e_n`, define:

```text
T(gamma) = g_en ... g_e2 g_e1
```

For a closed loop, this is a discrete holonomy:

```text
H(gamma) = g_en ... g_e1
```

Exact edge operators yield an exact loop observable. Potential ML roles include
local CNN loop features, graph cycle invariants, token transport, path-dependent
summaries, and consistency checks.

The appropriate current description is **holonomy-inspired exact relational
computation**. Physical interpretations such as gauge fields or topological
charge require separate mathematical and empirical justification.

## 7. Davis-style cache and gate

The Davis-Wilson work motivates separating bounded geometric observables from a
discrete residue:

```text
Gamma(x) = (Phi(x), r(x))
```

For SPU, this is an engineering adaptation, not an adoption of broader
conditional physics claims:

```text
Phi(x) = bounded geometric or relational summary
r(x)   = discrete sector, class, or algebraic residue
```

A candidate execution pattern is:

```text
x_t -> s_i -> x'_t -> Gamma -> (Phi, r) -> G -> x_(t+1)
```

The Weyl/Coxeter operator proposes an exact transformation; the cache observes
it; and the gate makes a deterministic admissibility, compression, or routing
decision. The gate's rule, width, overflow/quotient semantics, and
information-loss behaviour must be specified and independently testable.

## 8. Approximate training, exact execution

Training may maintain logits over generators:

```text
p_i = softmax(theta_i)
```

Soft mixtures, Gumbel-softmax, or straight-through estimators may be used
under a future training contract. Compilation hardens each slot:

```text
g_i = s_argmax_j(p_ij)
w   = g_1 g_2 ... g_L
```

The training machinery is then discarded. The central hypothesis is:

```text
approximate continuous training -> exact deterministic program compilation
```

Approximate optimization does not by itself guarantee that task behaviour
survives hard compilation; that must be measured.

## 9. Neural-network boundary and efficiency

The initial target is not replacement of an entire transformer or CNN. The
question is which expensive learned transformations can be replaced by short
exact geometric programmes without unacceptable loss of capability.

Candidate roles include projection, feature transformation, routing, token
transport, structured positional operations, local convolutional symmetry,
state compression, and admissibility gating.

The basic cost comparison is:

```text
dense transform
    vs
L * exact-generator cost + state traffic + control/decode overhead
```

Experiments must measure task performance, word length, state size, model
storage, integer operations, latency, memory traffic, hardware resources, and
physically measured energy where available. Opcode width alone is not model
complexity; complexity moves into word length, state representation, and
routing.

## 10. Hardware interpretation

```text
primitive operations = exact generators and gates
program             = finite primitive word
compiler             = learns or constructs the sequence
runtime              = executes exact discrete instructions
hardware             = deterministic functional units
```

Generator encodings are small:

```text
finite E8       -> 8 generators  -> 3-bit code
affine E8^(1)   -> 9 generators  -> 4-bit code
E10             -> 10 generators -> 4-bit code
```

These widths do not establish a model or hardware advantage.

## 11. Verification philosophy

For Coxeter execution, verify:

```text
s_i^2 = 1
(s_i s_j)^m_ij = 1
```

The verification set should include generator involution, braid relations,
lattice membership, invariant preservation, software/reference agreement, RTL
agreement when RTL exists, deterministic replay, and cross-platform bit
identity where applicable.

Formal verification may eventually provide stronger evidence than brute-force
enumeration of enormous state spaces. Exhaustive testing must be scoped to a
frozen finite-width domain and must not be described as exhaustive verification
of an unbounded group or lattice.

## 12. Initial experiment: Stage E8-0

1. Implement the eight simple `E8` reflections.
2. Verify all required Coxeter relations exactly.
3. Fix a word length `L`.
4. Give each word position eight trainable generator logits.
5. Train on a small, nontrivial task.
6. Harden every slot into a discrete generator.
7. Remove continuous training machinery.
8. Execute the exact word.
9. Compare with a small conventional baseline.
10. Measure quality and complete computational cost.

The first question is:

> Can useful learned behaviour be compiled into a short exact group programme?

Only a positive, reproducible result should justify progressively larger
experiments.

## 13. Research discipline

### Established mathematics

Coxeter relations, finite `E8` Weyl structure, affine Weyl groups, discrete
path composition, and finite quotient rings belong here when supported by
appropriate references and exact checks.

### Proposed architecture

Learned Coxeter programmes, Davis-style gates, holonomy-based token
relations, affine translation programmes, and hyperbolic routing belong here.

### Experimental result

Trained word length, task accuracy, exact replay, FPGA utilization, latency,
power, and dense-baseline comparisons belong here only after reproducible
evidence exists.

## 14. Working thesis

> Useful computation may be representable as finite programmes over small exact
> geometric operator sets, with approximate optimization confined to training
> and deterministic algebraic execution used for inference and hardware
> implementation.

Short form:

```text
geometry as executable structure
```

The objective is not to prove that one geometry solves every computational
problem. It is to determine which geometries provide useful exact primitives
for particular workloads.
