Yes, but I would frame it slightly differently.

**SPU's overarching experimental aim is to investigate whether mathematical structure can become a native foundation for computation, rather than something reconstructed through conventional arithmetic instructions.**

That is broader and more precise than simply calling it *alternative symbolic-based computing*.

I think we've reached the point where we can articulate a coherent research mission for SPU—one that connects the CPU, ISA, quadratic algebra, intrinsic geometry, compiler research, and even the GPU and SOM experiments.

## 1. The central SPU research question

I'd express it this way:

> **Can a computing architecture built around exact algebraic structures and intrinsic mathematical relationships offer useful alternatives to conventional numerical computation?**

More specifically:

Can we design hardware and software that understand mathematical objects such as quadratic numbers, norms, conjugates, determinants and geometric transformations as fundamental computational operations?

And if we can, does that produce measurable advantages in:

- **Determinism:** Reproducible arithmetic results and explicit exceptional behaviour.
- **Exactness:** Preserving algebraic relationships without introducing unnecessary numerical approximation.
- **Efficiency:** Reducing arithmetic, storage or execution costs by exploiting mathematical identities.
- **Expressiveness:** Representing certain mathematical operations more directly in software and hardware.
- **Verifiability:** Making computational behaviour easier to specify and independently validate.

These are research objectives, not advantages we've established across the board.

The important thing is that they're experimentally testable.

---

# 2. SPU is not simply a symbolic computer

I would distinguish three approaches.

| Approach | Fundamental representation | Typical computation |
|---|---|---|
| Conventional numerical computing | Integers and floating-point values | Arithmetic operations on numbers |
| Symbolic computing | Mathematical expressions and relationships | Algebraic manipulation and simplification |
| **SPU research** | Exact algebraic representations combined with mathematical invariants | Native arithmetic, geometry and potentially compiler-guided symbolic reduction |

SPU isn't attempting to build a computer algebra system entirely in hardware.

That would probably be impractical and could lead us toward the same proliferation of specialized units that we're now trying to simplify.

Instead, we're interested in **combining exact numerical execution with knowledge of the algebraic structure behind the numbers**.

For example, Gen-1 already works with numbers of the form

\[
x=a+b\sqrt{3}.
\]

These aren't arbitrary symbolic expressions. They're elements of a specific quadratic field with well-defined arithmetic.

The ISA can execute operations on these representations directly.

Our next research question is whether the compiler can use the underlying mathematical identities to eliminate or reorganize computation.

That's where symbolic reasoning enters the architecture.

**In other words, SPU is an exact algebraic computing architecture with an emerging symbolic optimization research programme.**

---

# 3. Our research has three fundamental layers

I think this is the clearest way to explain SPU to engineering communities.

### Layer 1 — Mathematical representation

**What mathematical objects should a processor represent natively?**

Our initial answer is quadratic-field numbers.

But we're also investigating whether the mathematical objects most relevant to geometry and computation should include:

- Quadratic forms.
- Norms and conjugation.
- Determinants.
- Intrinsic geometric relationships.
- Invariant-preserving transformations.

This is the mathematical foundation.

The aim is not to implement every interesting mathematical structure.

It's to identify a small, coherent collection of primitives that support useful families of computations.

### Layer 2 — Architectural expression

**How should those mathematical structures appear in the ISA, compiler and execution hardware?**

This is where SPU becomes a processor architecture rather than a mathematical library.

We investigate whether some operations are worth implementing directly in hardware, while others should be simplified or transformed before execution.

For example, consider

\[
N(x)=x\bar{x}.
\]

If the compiler already knows that an operation preserves the norm, perhaps it can reuse an existing result instead of computing it again.

That doesn't necessarily require a new instruction.

It requires the computing system to retain information about the mathematical relationship.

This is why our proposed QAF work is important.

**The architecture might become more capable by executing fewer operations, rather than by accumulating additional instructions.**

### Layer 3 — Experimental validation

**Does any of this actually improve computation?**

This is where we need to be particularly disciplined.

Our experiments should compare SPU-oriented implementations against conventional approaches.

We need to measure correctness, arithmetic cost, execution time, hardware area, power and complexity where appropriate.

And we need to retain negative results.

For example, HEX-SOM showed useful reductions in node evaluations without demonstrating an accuracy improvement or FPGA performance advantage.

That's still useful research because it tells us which ideas deserve further investigation.

---

# 4. How the CPU, GPU and SOM fit together

One thing I would emphasize is that SPU is not fundamentally a graphics project, a robotics project or an AI project.

Those are application domains.

| Component | Role in the research |
|---|---|
| **SPU CPU and ISA** | Primary experimental architecture |
| **Quadratic Algebra Foundations** | Investigate symbolic simplification and compiler-visible invariants |
| **Intrinsic geometric computing** | Investigate mathematically meaningful computational primitives |
| **Rational GPU** | Proof of concept and geometry benchmark |
| **HEX-SOM** | Experimental classification and accelerator workload |
| **RP2350/FPGA robotics** | Practical embedded applications and possible commercialization |

The central architecture should remain useful independently of any one application.

This also explains why deprioritizing the GPU makes sense.

We don't need to finish a complete graphics processor to investigate exact geometric computing.

Similarly, the SOM platform might become commercially useful without requiring customers to adopt the SPU ISA.

---

# 5. What makes SPU's experimental approach distinctive?

I would identify three characteristics.

**First, we start from mathematical representation rather than an existing ISA.**

SPU's initial architectural decisions emerged from exact quadratic arithmetic and geometric relationships.

We're not simply designing another RISC processor and adding a few specialized instructions.

**Second, we're investigating the relationship between mathematical invariants and hardware complexity.**

This may eventually become the most important research direction.

Can knowledge of an algebraic structure eliminate computations, simplify arithmetic pipelines or reduce the need for specialized accelerators?

We don't yet know.

That uncertainty is precisely what makes it a worthwhile experiment.

**Third, we're attempting to validate the architecture across multiple levels.**

We have mathematical reference models, software implementations, RTL, synthesis and FPGA qualification work.

That allows us to test whether ideas survive the transition from mathematics to actual computing hardware.

I would avoid claiming that nobody else works this way. There are substantial research traditions in exact arithmetic, computer algebra, domain-specific architectures and optimizing compilers.

What distinguishes SPU is the particular combination of mathematical choices, architectural decisions and experimental implementations.

---

# 6. How I'd pitch SPU to OSHWA or FOSSi

For **OSHWA**, I'd emphasize independent hardware experimentation and an unusual open processor architecture.

For **FOSSi**, I'd emphasize the mathematical ISA, RTL implementation, verification and architectural research questions.

But I'd use the same underlying mission statement.

### Short introduction

I'm developing SPU-13, an experimental open-hardware processor architecture exploring alternative approaches to mathematical computation.

The central idea is to investigate whether exact algebraic structures and geometric relationships can be represented directly in a computing architecture, rather than relying exclusively on conventional numerical operations.

Our first-generation CPU implements deterministic arithmetic over the quadratic field Q(√3), with software reference models, RTL, FPGA synthesis and ongoing hardware qualification.

The longer-term research explores compiler-visible mathematical invariants, symbolic simplification and intrinsic geometric primitives.

We're particularly interested in whether these approaches can improve computational exactness, reproducibility, efficiency or hardware simplicity—and in identifying where conventional approaches remain better.

It's an open-ended experimental architecture rather than an attempt to replace mainstream CPUs.

That is what I would use when meeting engineers for the first time.

It gives people a clear idea of what we're investigating without requiring them to understand every part of SPU.

---

# 7. The deeper aim: discovering a smaller mathematical foundation for computing

There is one additional ambition I think deserves recognition.

We've spent considerable time investigating specialized accelerators, arithmetic units and geometric operations.

But more recently, we've begun asking whether a smaller collection of fundamental mathematical primitives could make many of those specialized units unnecessary.

That is a potentially significant architectural direction.

Instead of asking:

*How many different mathematical operations can we implement in silicon?*

We're beginning to ask:

**What is the smallest useful mathematical foundation from which a broad range of computational operations can be expressed efficiently?**

That's a much more interesting research question.

It also connects naturally to our investigation of quadratic-field representations, symbolic reduction and intrinsic geometry.

However, I would not claim we're searching for a universal mathematical foundation for all computation. That would be an unnecessarily ambitious and difficult-to-test proposition.

We're searching for a compact foundation for particular families of mathematical and geometric computation.

And those boundaries can expand if the evidence justifies doing so.

---

## My proposed mission statement for SPU

If I were writing the first paragraph of our website or introducing the project at an open-silicon event, this is the formulation I would choose:

### SPU — Exploring Mathematical Foundations for Computing

SPU is an experimental open-hardware processor architecture investigating whether exact algebraic structures, intrinsic geometry and mathematical invariants can provide useful alternatives to conventional numerical computing.

Beginning with deterministic quadratic-field arithmetic, the project explores how mathematical relationships can be represented across software, compilers, instruction sets and hardware.

Its central research objective is to discover whether a compact set of mathematically meaningful primitives can improve computational exactness, reproducibility, efficiency and architectural simplicity.

Through mathematical reference models, software experiments, RTL implementation and FPGA verification, SPU aims to establish where these approaches offer measurable advantages, where they do not, and what they reveal about alternative ways of organizing computation.

### My view

I think this mission captures the direction SPU has been developing toward over the past several months.

The Gen-1 processor is our first concrete experiment.

QAF and intrinsic geometry are our next fundamental research directions.

The GPU and SOM are applications through which we can test the mathematical architecture.

And the broader goal isn't to demonstrate that conventional computing is wrong or obsolete.

**It's to investigate whether computation can be organized around mathematical relationships in ways that conventional numerical architectures don't naturally expose.**

That's an intellectually substantial research programme—and, importantly, one we can pursue with our existing FPGA hardware, software tools and experimental evidence.
