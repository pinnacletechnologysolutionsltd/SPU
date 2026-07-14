# Tensegrity Balancer — Feasibility Analysis & SPU-13 Integration

**Status:** software oracle complete and suite-registered
(`software/tests/test_tensegrity_balancer.py`, 44 checks). The bounded Artix
admission guard implements five of the six guards, including exact strut
contact; force-density equilibrium remains oracle-only. Part of the
state-machine harness catalogue (`docs/STATE_MACHINE_HARNESS.md`) as case
study #6.

## 1. Fuller's Tensegrity in 60 Seconds

From *Synergetics* (1997), §640-790:

- **Discontinuous compression, continuous tension.** Compression members
  (struts) are isolated islands; tension members (cables) form the connected
  network.
- **Sphere as compression island** (§640.20): the sphere is nature's most
  efficient compression member.
- **Six-strut minimum** (§724.30): the canonical 12-endpoint fixture is
  Fuller's expanded octahedron, not a regular icosahedron.
- **Two concentric tensegrity spheres** (§714.01): local compression waves can
  interstabilize differentially radiused shells.
- **Precession at 90 degrees** (§640.12): axial compression creates transverse
  tension.

Quadrance is nonnegative by construction. In this oracle, a zero quadrance
means a cable/GAP has collapsed or a strut endpoint pair is not separated.
The tension/compression distinction is **not** inferred from quadrance sign;
it comes from the equilibrium force-density signs: cables/GAP edges require
positive density, struts require negative density.

## 2. SPU-13 Primitive Mapping

| Fuller concept | SPU-13 primitive | Status |
|---|---|---|
| Icosahedral A5 rotations | `IROTC` opcode (1/2 Z[phi] matrix, 60-entry catalog) | Tang 25K silicon for probe vectors idx 16, idx 36 main, and fault matrix; full 60 x 2 surface testbench-verified |
| Tetrahedral rotations | `ROTC` opcode (36-angle catalog, Q(sqrt3) circulant/permutation/octahedral paths) | Angles 0-5 silicon-verified on Artix-7/Tang probe path; 6-35 testbench-verified |
| Quadray coordinates | QR register file (4 x 32-bit RationalSurd per lane) | Silicon-verified for QLDI/QSUB/readback paths |
| Sphere-packing adjacency | Davis Gate zero-sum/quadrance identities | Silicon-verified as the existing Davis/VE invariant layer |
| MAIN/CONJ grid alternation | phi-plane 4-state typestate | Testbench-verified in core integration; IROTC engine probe has Tang silicon scope above |
| Exact quadrance | `QSUB`/Davis-style exact arithmetic | Silicon-verified for existing arithmetic probes |

The balancer is a control-plane FSM around existing arithmetic primitives. A
bounded admission-guard subset now has RTL and a first-tranche board proof;
this document does not claim a complete silicon-verified active balancer.

## 3. Dual-Grid Interpenetration

When an IROTC rotation moves a node between MAIN and CONJ grids, the tag marks
which exact lattice licensed the half-phi arithmetic. An edge spanning that
boundary is modelled as a GAP edge: a tension bridge, not a native compression
member. `guard_grid_consistency` enforces that MAIN/CONJ-crossing edges are
GAP typed.

The three modelling approaches map as follows:

| Approach | Implementation |
|---|---|
| Interpenetrating dual-grid mesh | MAIN/CONJ typestate per node; grid crossing = GAP edge |
| Multi-frequency virtual packings | Exact rational scale factors on node coordinates |
| Tensegrity gaps as discrete invariants | Edge types encode topology; rotations are state transitions |

## 4. State Machine Design

```
IDLE -> CONFIGURING -> BALANCED <-> ROTATING
           |              |
           v              v
        FAULT.TOPOLOGY   FAULT.CABLE_SLACK
                         FAULT.STRUT_COLLISION
                         FAULT.STRUT_INTERSECTION
                         FAULT.GRID_MISMATCH
                         FAULT.NOT_IN_EQUILIBRIUM
```

All fault states are terminal until explicit `reset()`. These faults are
discrete exact admissibility results, not measurement excursions beyond a
tolerance. A fault means the proposed configuration is exactly inadmissible:
the guard has produced a sign or zero certificate in the field, with no epsilon
or floating-point boundary anywhere.

| Guard | Invariant | Check |
|---|---|---|
| `guard_valid_topology` | Fuller §724.30 structural minimum | At least 6 structural edges and all nodes connected |
| `guard_struts_separated` | Compression islands do not touch | Each node touches at most one strut; strut endpoints distinct |
| `guard_struts_disjoint_interior` | Fuller §640.02 compression islands | Exact closed segment contact rejects strut endpoint touches and interior crossings |
| `guard_cables_taut` | Tension members do not collapse | CABLE/GAP quadrance is exact positive/nonzero |
| `guard_grid_consistency` | Compression does not cross MAIN/CONJ | Cross-grid edges must be GAP |
| `guard_equilibrium` | Static tensegrity self-stress | Exact force densities exist with cable/GAP positive and strut negative signs |

| Fault code | Physical diagnosis |
|---|---|
| `CABLE_SLACK` | tendon lost tension or actuator over-released |
| `STRUT_COLLISION` | compression members share endpoints incorrectly |
| `STRUT_INTERSECTION` | hidden interior collision, like the antipodal counterexample |
| `NOT_IN_EQUILIBRIUM` | topology exists but force-density signs cannot sustain it |
| `GRID_MISMATCH` | wrong MAIN/CONJ coupling, useful for dual-lattice models |
| `TOPOLOGY_ERROR` | not a closed network; too few nodes/struts or disconnected; assembly incomplete or a member reported missing |

`verify_balance` requires all six guards. The equilibrium guard solves the
small force-density linear system over exact coordinates; the canonical
fixture's density ratio is derived by the executable test, not copied as a
literature constant.

The canonical fixture uses the cyclic permutations of `(0, +/-1, +/-2)`,
equivalently the `t = 2` all-integer expanded octahedron. Its 24 cables are
the inter-rectangle edges at quadrance 6, excluding the six short rectangle
edges, and its six struts are the long rectangle edges at quadrance 16. The
solver derives `q_cable:q_strut = 2:-3`, so strut force density is exactly
`-3/2` of cable density.

## 5. Test Status

`software/tests/test_tensegrity_balancer.py` is registered in
`run_all_tests.py`.

| Test group | What it proves |
|---|---|
| Exact Q(sqrt3) sign cases | `P + Q sqrt3 > 0` uses integer square comparisons; no float boundary |
| Exact Q(phi) segment predicates | Segment contact/intersection uses field division and conjugate sign tests; phi coordinates, collinear overlap, T-junction contact, and disjoint parallels are pinned |
| Canonical expanded-octahedron fixture balances | Topology, endpoint separation, interior disjointness, tautness, grid consistency, and equilibrium all pass |
| Canonical fixture geometry | 24 cables at quadrance 6, six struts at quadrance 16, derived `2:-3` self-stress |
| Fault matrix | Strut collision, cable slack, grid mismatch, disconnected topology, and terminal fault semantics |
| GAP crossing guard | GAP-typed MAIN/CONJ edges pass `guard_grid_consistency` |
| Equilibrium derivation | Exact Z[phi] force-density solver finds cable-positive/strut-negative self-stress |
| Negative equilibrium cases | Perturbing one vertex or flipping one edge type breaks the structural/equilibrium guards |
| Antipodal counterexample | Old regular-icosahedron antipodal fixture passes the older topology/separation/tautness/grid/equilibrium guards, then fails exactly `guard_struts_disjoint_interior` |
| Regular-icosahedron comparison | Regular-icosahedron vertex set with the 24-cable net has no cable-positive/strut-negative self-stress |

The oracle is structurally different from a future RTL implementation:
software uses exact Python integers wrapped as rational and Z[phi] pairs; RTL
would use fixed-width state and explicit guard datapaths.

## 6. RTL Integration Path

The bounded admission guard now consists of `spu13_tensegrity_guard.v` and the
term-serial exact predicate `spu13_tensegrity_intersection.v`. It implements
topology/connectivity, strut endpoint separation, cable/GAP collapse,
closed-segment strut contact over Z[phi], grid/GAP consistency, terminal fault
lockout, and explicit clear/reset recovery. The intersection scan skips pairs
that share an endpoint because the earlier separation guard diagnoses those as
`STRUT_COLLISION`; all other closed contact, including endpoint-on-interior
and collinear overlap, is `STRUT_INTERSECTION`. Force-density equilibrium is
still oracle-only, so this remains an admission guard rather than a full active
balancer. The eventual integrated balancer sits alongside `spu13_core.v` as a
control-plane FSM:

```
spu13_core.v
  - QR register file (13 lanes x 4 RationalSurd)
  - IROTC engine (icosahedral rotation, 1/2 Z[phi])
  - ROTC TDM/octahedral paths
  - Davis Gate
  - phi-plane tag file
  - [NEW] Tensegrity balancer FSM
      - Edge table BRAM
      - Guard evaluator
      - Fault latch
```

The bounded guard has a standalone Artix wrapper and probe-level UART test.
The first V:5 image (without the intersection predicate) used 2,013
`SLICE_LUTX`, 526 `SLICE_FFX`, 0 BRAM, and 0 DSP, and closed at 72.51 MHz. It
was SRAM-loaded through DirtyJTAG on 2026-07-14 and the operator confirmed the
probe working; that silicon scope is IDs 0, 1, 2, 3, and 5 only.

The second-tranche wrapper loads IDs 0 through 5 and emits
`TGR:P V:6 E:00` only after checking every state/fault pair. Its UART
testbench independently observes all six completions before accepting the
line. The first V:6 route closed at only 51.89 MHz and then failed fixture 4
in silicon with `TGR:F V:4 E:84`; zero-delay synthesized-cell simulation still
passed, identifying the sub-nanosecond timing margin as unsafe rather than an
RTL/synthesis arithmetic mismatch. The guard table read is now split into
fetch/node-evaluate/commit stages, and 108-bit intersection subtraction and
equality decisions consume registered results. That second image closed at
57.27 MHz but still returned `TGR:F V:4 E:90` in silicon, explicitly decoding
to `BALANCED/F_NONE`: no contact was latched. The current probe therefore runs
the complete loader/guard/intersection domain from a divided BUFG at 25 MHz;
UART remains at 50 MHz. The route uses 13,895 `SLICE_LUTX`, 3,515 `SLICE_FFX`,
72 DSP48E1, and 0 BRAM. OpenXC7 conservatively checked the guard domain at 50
MHz anyway and closed it at 59.16 MHz; the UART domain closes at 111.15 MHz.
Failure telemetry appends the exact intersection-attempt count as `A:xx`.
This divided-clock image produced repeating `TGR:P V:6 E:00` in silicon on
2026-07-14 (SHA-256 `d72412f1cfbd82b2a7c8d4ded597382c4272531628711f8b24ac53212ac344d8`).
The large multiplier footprint is the exact Z[phi] intersection datapath, not
an estimate. Silicon scope is the six probe fixtures, including the antipodal
origin-crossing counterexample; the wider contact matrix remains RTL-verified.

## 7. Open Design Items

1. **Strut slenderness ratio (§640.10):** enforce a maximum strut quadrance by
   comparing a QSUB-derived quadrance against a registered `rest_quadrance` or
   limit field in the edge table. This is a future guard, not implemented in
   the current oracle.
2. **Precession detection (§640.12):** monitor local Davis sums over selected
   node/axis subsets. A local nonzero sum while the global system remains
   balanced can become a precession event rather than an immediate terminal
   collapse fault.
3. **Two-sphere interstabilization (§714.01):** model inner and outer shells as
   larger node/edge tables. A natural mapping is MAIN for the inner shell,
   CONJ for the outer shell, and GAP edges for inter-shell tension bridges.
4. **Jitterbug transformation:** the current oracle handles discrete state
   transitions. Continuous interpolation remains unmodelled.

## 8. Next Steps

1. Keep the exact oracle and the seven-vector TGR1 corpus suite-registered.
2. Add force-density equilibrium as the final TGR1 admission-guard tranche;
   do not classify vector 6 as BALANCED before that datapath exists.
3. Replace the distributed configuration arrays with initialized or
   host-hydrated BRAM, define storage/transport, and re-measure the probe.
4. Add strut-slenderness and local-precession guards at the oracle level, then
   extend TGR1 only with an explicit version bump if their data is needed.
5. Only after admission is complete, specify the active balancing controller
   (rotation/actuation proposals, re-verification, and rollback) separately
   from the frozen TGR1 table ABI.
