# SPU algebraic–geometric machine: research direction

Date: 2026-10-13. Status: PROPOSED architectural direction, not an execution contract.

## Documentation review

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/ALGEBRAIC_GEOMETRIC_MACHINE_RESEARCH_DIRECTION.md docs/SGN1_RESEARCH_SPECIFICATION.md docs/README.md
```

## Guiding question

Can an exact algebraic transformation be transported, composed and reversed
across a geometrically structured processing network without lossy numerical
materialization, while preserving deterministic and independently verifiable
machine state?

Develop representation, execution and communication through compatible
algebraic/geometric rules. Establish mathematical correspondence, useful
expressiveness and physical cost separately. Exactness alone establishes
neither compactness nor efficiency; message movement and transformation
execution each consume resources.

## Initial representation boundary

Start from z=(a+b√3)U^k, U=2+√3, and separately retain a Quadray address or
displacement q=(q0,q1,q2,q3). The Pell exponent is not a spatial coordinate.
The proposed richer state S=(a,b,k,I) requires a reviewed definition of I:
which metadata is derived, how it is validated and when it changes.
Do not trust an incoming invariant tag as proof of the represented value.

Distinguish numerical values, transformation descriptors and symbolic expressions.
The restricted AOR tuple is not a general expression grammar, nor a universally
canonical representation. Restoration of a value and restoration of every
stored field are different acceptance conditions; specify both where required.
Canonical-zero rules and bounds remain explicit even for forward/inverse tests.

The [AOR symbolic-processor roadmap](../spu_strategy/AOR_SYMBOLIC_PROCESSOR_ROADMAP_2026-10-13.md)
retains its software evidence and future symbolic-state gates. The
[SGN-1 specification](SGN1_RESEARCH_SPECIFICATION.md) defines the corrected
Quadray/FCC domain and deterministic-network proposal. Neither proves a unified
processing network. Existing isolated geometry-oracle work remains in scope.

## Three complementary research tracks

| Track | Question | Architectural role |
|---|---|---|
| AOR | Which algebraic relationships can machine state retain compactly? | Representation |
| SGN | Can exact geometry organize deterministic movement of state? | Communication |
| D4/E8 | Do lattice symmetries provide useful native operations or transformation descriptors? | Symmetry |

The [D4/E8 discovery preparation](../spu_strategy/contract_d4_e8_symmetry_discovery_preparation_2026-10-13.md)
defines proposed D0 algebra, D1 symmetry, D2 SPU mapping and D3 comparative
software gates. All remain NOT RUN as this new discovery campaign. Preserve
earlier D4 results and their task-specific limits; they establish neither E8
qualification nor integration with AOR or SGN. Require rank-eight coordinates
for E8, explicit exact scaling and conventional representation baselines.

Keep backend legality and CPU placement primary, AOR-S1 proof/oracle review
next, and SGN mesh/cost under its separate authorized budget. D4/E8 stays in
documentation preparation. Promote operations toward RTL only after proofs
and comparative software evidence identify a useful bounded subset.

## Five proposed research gates

| Gate | Deliverable | Required demonstration before promotion |
|---|---|---|
| G1 | Unified mathematical reference | Exact AOR semantics and independent Quadray coordinates; explicit operation/address mapping, bounds and equality rules |
| G2 | Distributed software simulation | Qualified SGN graph/routing; transported algebraic states match an independent oracle after composition and reversal |
| G3 | One bounded processing-element RTL model | Local state, restricted transformations, port selection, representation tags and ready/valid ownership; atomic failure and reset checks |
| G4 | Standalone small RTL network | Reviewed four/eight-node graph; simultaneous traffic, arbitration, reset, backpressure, delivery and invariant checks |
| G5 | Optional SPU-13 service | Verified CPU/network interface, initially a proposed memory-mapped command queue with defined ownership and completion |

These gates are proposals, all NOT RUN as unified-machine experiments. Each
needs reviewed source scope, independent fixtures, exact commands and its own
authorized execution budget. Existing AOR or SGN component checks do not mark
G1 or G2 complete. G3/G4 functional RTL verification, device-specific synthesis,
legal routing/timing and board observation are separate evidence claims.

## First proposed end-to-end falsifier

After graph and routing qualification, inject an AOR value at a source node,
compose a forward Pell step, forward through a specified legal Quadray port,
then apply the inverse at the receiving node. Independently check destination,
delivery multiplicity, algebraic value, required representation fields and
the complete deterministic machine trace. Require valid bounded intermediates;
do not assume a final inverse cancels an earlier overflow or resource refusal.

Negative controls must detect a wrong exponent, wrong port, duplicate/drop,
incorrect invariant metadata and partial state commit. A budget-limited equality
check is undecided, not a proof of inequality. Tetrahedral port permutations
and Pell boosts remain distinct operations; no shared group action is assumed.
Define a reflection on algebraic state before testing it, rather than inferring
one from a reflection of the graph.

## Questions that should determine RTL scope

Identify which transformations remain compact, which execute locally, and which
force alignment, normalization or coefficient materialization. Measure retained
state, temporary storage, work and communication under matched semantics and
resource limits, including adversarial growth. Specify refusal without partial
writes. Keep general or exceptional computations on the host initially.

For G3/G4, review packet representation/version tags, finite numerical bounds,
buffer ownership, completion validity, reset epochs and cancellation. Reset must
not turn stale traffic into a fresh accepted request. Use PSS-1/PSS-1R lifecycle
lessons, but independently qualify the new interface and backpressure protocol.
Unbounded SGN software queues do not prove finite-buffer deadlock freedom.

## Priority and physical boundary

Finish the Surd register paper, qualify the existing physical backend and bring
the current Surd CPU onto Artix-7. Preserve active placement inputs and budgets.
This note starts no unified-machine implementation, RTL or hardware campaign.

An eventual ASIC is a possible physical realization after logical qualification.
A small FPGA network does not demonstrate physical IVM placement or a wiring,
energy, speed or universal-expressiveness advantage. Asynchronous execution and
custom spatial layouts require separate protocols and physical evidence.
Preserve hardware claim limits in the [evidence ledger](hardware_evidence.md).
