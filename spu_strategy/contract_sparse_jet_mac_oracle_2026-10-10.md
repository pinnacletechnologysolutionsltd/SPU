# Sparse Jet MAC software contract — 2026-10-10

```bash
python3 -B software/tests/test_sparse_jet_mac_oracle.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/SPARSE_JET_MAC.md software/tests/sparse_jet_model.py software/tests/sparse_jet_reference.py software/tests/sparse_jet_protocol.py software/tests/test_sparse_jet_mac_oracle.py spu_strategy/contract_sparse_jet_mac_oracle_2026-10-10.md
```

Owner authorizes resolving the five reviewed issues and validating software,
including the proposed completion protocol. One isolated full qualification
attempt is authorized: 7,200 seconds wall-clock and cumulative, one slot.
No retry or timeout extension follows from failure or timeout.

1. Use A31[eps]/(eps^(N+1)), a split algebra, canonical four-lane residues.
   Validate arithmetic at N=2/N=4. Test N=15 tag width only. Nonunits are
   valid MAC operands; inverse rejection stays separate. MAC fault remains 0.
2. Valid windows are 0<=lo<=hi<=N or [N+1,0]. Monitor zero promises outside
   tags. Reject malformed/noncanonical inputs in software; hardware trusts
   sequencer provenance. TAG_BITS=ceil(log2(N+2)); widen sums one extra bit.
3. Multiply tags add/clamp; empty inputs or lo>N return canonical empty.
   Addition uses tag union with empty identity. Never sharpen by values.
4. Enumerate all 305 ordered window pairs. Independently check Cauchy values,
   order-major schedules and exact counts. Preserve old approximate digon
   workload tables; do not infer full-workload speedup from primitive counts.
5. Accept only in IDLE and capture inputs. Ignore starts while busy and on
   retirement. Issue one multiply, wait for its response, then advance.
   Hold busy through retirement; drop it with a single-cycle done pulse.
   Empty/add paths must take at least one busy cycle. No timeout completion.
   Reset cancels and clears; shared fabric must reset/drain before reuse.
   Untagged stale responses in a new WAIT are outside this guarantee.
6. Use independent exponent-basis arithmetic and rectangular enumeration.
   Compare fixed/general production jet oracles. Exercise basis/extrema,
   cancellation, zero divisors, random conforming windows, variable response
   latency, reset in ISSUE/WAIT/RETIRE, withheld response and rejected tags.
   Negative controls must detect missing issue, early busy drop, duplicate
   completion and incorrect result/tag.
7. Freeze the previously qualified D4 snapshot plus these scoped files.
   Run fresh focused/scoped/repository, trace, math and separate 25 MHz Padé
   gates through the detached runner; record source/dependency hashes,
   individual exits and exactly one terminal marker. End the launch turn.

**Status: COMPLETE — frozen software scope**, reviewed 2026-10-11.
Qualification_01: COMPLETE, exit 0, 2,169 seconds; all 13 gates passed.
See [closure record](../build/sparse_jet_mac/qualification_01/qualification_review.json).

Software PASS qualifies this bounded model contract only;
it does not authorize sparse RTL implementation or qualify the dense RTL
handshake. REGEN, Surd, WF, transports and production arithmetic stay outside
the repair. Integrated mapping acceptance is independently legal routing,
complete required timing coverage and PASS at 25 MHz. The separate integrated
attempt confirmed 234 DSPs in synthesis/packing and timed out in placement;
its routing and timing acceptance remain unresolved.
