# SGN-1 fourth software increment: synchronous scheduler implementation

Date: 2026-10-13. Status: IMPLEMENTED; revised preflight PASS;
serialized predecessor regressions passed; full qualification prepared separately.
Roles: frozen draft, halt-and-flag implementation, independent audit.

## Short preflight commands

```bash
python3 software/tests/test_sgn1_scheduler_preflight.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/sgn1 software/tests/test_sgn1_scheduler_preflight.py spu_strategy/contract_sgn1_scheduler_implementation_2026-10-13.md docs/SGN1_RESEARCH_SPECIFICATION.md
```

Use one short preflight with a 60-second external limit, preserving stdout,
stderr, exit and source/fixture hashes in a new child of
`build/sgn1/scheduler_20261013/`. It exercises implementation checks, not complete
qualification. Freeze the manifest before running. A failed preflight halts for
a named correction; do not launch full qualification on partial success.

## Authority and scope

The owner's subsequent "Let's begin" authorizes isolated scheduler implementation
and short preflight now, superseding the implementation wait in the
[preparation packet](contract_sgn1_scheduler_preparation_2026-10-13.md).
Full scheduler qualification still follows COMPLETE symmetry and routing
regressions in the agreed serialized order. No scheduler campaign is launched
by implementation. Preserve the preparation packet's fixture/protocol hashes.

New source scope: `software/research/sgn1/packets.py`, `topology.py`,
`node_service.py`, `simulator.py`, `schedule_reference.py`, `conservation.py`,
`trace_checker.py`, `scheduler_fixtures.py`, and
`software/tests/test_sgn1_scheduler_preflight.py`. No production SPU, AOR,
hierarchy, reduction, stencil, RTL, board or CPU-interface changes.

## Reviewed semantics and independent checking

The implementation uses immutable packet records, deque inbox/fanout state,
sorted admission and next-tick committed transmissions. One service per node
shares the frozen alternating inbox/fanout allowance. Unicast local delivery,
wavefront first visit and duplicate suppression each consume a complete service.
Only first visits add wavefront payloads; fanout includes every present port.

The independent checker uses dictionary/list states, literal reference nodes,
squared-distance adjacency and BFS to check the first improving port. It imports
neither simulator, packet class, service, topology generation nor local selector.
Its whole-trace comparison covers admission prefixes, services, preferences,
exact updates, seen sets, queue prefixes and synchronized link commit.

Per-identity conservation uses original input payload/destination labels. Check
queued, in-flight and delivered unicasts; wavefront roots plus created tasks
equal queued/pending/in-flight copies plus first visits and suppressions. Check
unique delivery separately. Component traversal independently supplies final
wavefront totals. Measure storage peaks, service operations and admission-sort
comparisons. These are host-model costs, not physical wire/energy claims.

## Preflight acceptance and halt conditions

Check generated topology against the independent graph oracle. Exercise both
literal scheduling fixtures and reversed node iteration, future injection and
tick-limit distinction, strict injection validation, and checker mutations.
Retain named counterexamples for loss/duplication, wrong updates, premature seen
marking, dropped fanout, wrong preference, cost-free duplicate service,
incorrect commit and missing observations. An absent observation is UNVERIFIED.
No full-suite, all-traffic, all-pair or three-seed scheduler PASS follows from
this short preflight. Halt on any positive mismatch or escaped negative control.

Next execution packet: freeze full fixture coverage, trace/hash-seed comparisons,
negative controls, source identities, exact runner and a bounded detached budget.
Complete the two serialized predecessor regressions before launching it.

Initial preflight 01 passed six tests. Review then identified that the checker
also needed to reject redundant ticks after drainage; add a falsifiable test
and exact first-drained-tick check. Preserve preflight 01, freeze revised sources
and run preflight 02 under the same 60-second limit. This is a short revised
implementation check, not another expensive campaign or full qualification.

Preflight 02 passed seven tests in 0.211 seconds. Retained evidence under
`build/sgn1/scheduler_20261013/preflight_02/` includes the pre-run source manifest,
stdout/stderr, eleven named first counterexamples and the mixed-wavefront trace.
All-traffic/all-pair and hash-seed qualification remains NOT RUN.

Both predecessors subsequently completed successfully. The
[bounded qualification packet](contract_sgn1_scheduler_qualification_2026-10-13.md)
freezes the next source snapshot, coverage and detached budget. Its snapshot
preflight passes seven tests and sixteen controls after immutable-oracle caching;
full qualification remains pending its own terminal result.
