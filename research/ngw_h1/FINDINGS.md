# NGW-H1 — Exact hexagonal memory layout and weighting comparison

**Status: COMPLETE (owner decision 2026-10-20), negative performance findings preserved.**
Eisenstein aperture-7 addressing is kept as a qualified mathematical primitive. Dense axial and
Morton are kept as the leading physical-layout candidates. Nguyen weighting remains an optional
policy hypothesis, not a planned hardware feature. NGW-S1 (SOM-assisted residency) is on HOLD
until a scan-resistant policy and a shifting-region workload show a real learning opportunity.

2026-10-20. Class A host-only experiment (AGENTS.md §4.3,
[execution policy](../../spu_strategy/RESEARCH_EXECUTION_POLICY.md)), owner-approved
scope. It reuses the H2 Eisenstein arithmetic read-only. This is a **model-only cache
simulation**; no FPGA, latency or speedup claim follows from it.

**Freeze.** `spec.py` fixed the scene, packing, capacity, associativity, latencies,
tie-breaking, the structural weight and the adaptive formula before any cache
result. SHA-256 `5f1dba3e991e023896e8c85d5bbb29ddcaf570716ff8f69c5b56cf58db5c2f8b`
was recorded at 2026-10-20T08:54:47+13:00 and re-verified unchanged immediately
before the single results run. The address-overhead definitions (`scene.py`
docstring) were also written before any result. The scene size was checked
(node counts only) before freezing.

```bash
timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/ngw_h1/test_ngw_h1.py'   # 7 groups PASS, 0.5 s
timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/ngw_h1/run.py'           # exit 0, 0.22 s
```

## Setup (from spec.py)

**Scene.** 5 aperture-7 levels, π = 2 − ω, digits {0, ±1, ±ω, ±ω²}. A cell refines when it
is close to the focus (3,1), giving 372 nodes and 319 leaves spread over several levels.
Subtree sizes vary within each level, so structural weight is not vacuous.

**Memory model.** 16-byte records, 64-byte lines (4 records per line), 16 lines as
4 sets × 4 ways. Hit costs 1 and miss costs 20. Estimated cost =
hits + 20·misses + address operations.

**Layouts.**

| Layout | Ordering |
|---|---|
| Dense axial | (level, b, a) |
| Morton | Z-order on (a, b) within each level |
| GBT | Preorder of the aperture-7 tree |
| Tiled | 2×2 tiles over a padded bounding box per level |

**Policies.** All ties fall back to LRU.

| Policy | Evicts |
|---|---|
| LRU | Least recently used line |
| LFU | Lowest in-residency hit count |
| Structural | Lowest S(line) = Σ subtree sizes of the line's records |
| Adaptive | Lowest S(line) + 4·(in-residency count) |
| Belady | Farthest next use in that layout's *own* line stream |

## Verification

- **Digits.** The seven digits form a complete residue system mod π. All 7⁵ = 16,807 domain points encode and decode uniquely. Every 3-digit string round-trips. A far point is correctly outside the domain.
- **Parent/child.** Each parent equals its children's address prefix. Each level-1 cell owns exactly 7 fine points, giving an exact logical partition of the domain.
- **Identity.** Every layout is a bijection onto the 372 cells, and every one of the 3,982 workload accesses returned the requested (a, b, level) under every layout.
- **Cache model.** Hand-computed traces pass (LRU thrashing on 5 lines in a 4-way set, Belady 6 misses, full utilisation, structural retention). Belady equals an exhaustive minimum-miss search on 40 random streams and is never beaten by an online policy.

## Results (misses; LRU / Belady)

| Workload (accesses) | axial | morton | gbt | tiled |
|---|---:|---:|---:|---:|
| neighborhood (1927) | **91** / 91 | 96 / 92 | 220 / 150 | 717 / 446 |
| zoom (117) | **12** / 12 | 14 / 14 | **12** / 12 | 17 / 17 |
| visibility (89) | 47 / 36 | **32** / 29 | 66 / 48 | 83 / 66 |
| pan (136) | 20 / 19 | **12** / 12 | **12** / 12 | 36 / 24 |
| gbt_hostile (756) | 111 / 83 | **108** / 87 | 147 / 110 | 231 / 205 |
| thrash (957) | 837 / 635 | **824** / 609 | 842 / 616 | 927 / 783 |

The full grid, including miss rate, transferred bytes (= misses × 64), utilisation,
address operations and cost, is printed by `run.py`.

**Address-encoding overhead.**

| Layout | Ops per access | Extra storage |
|---|---:|---|
| Axial | 9 | 2,976 B index |
| Morton | 42 | 2,976 B index |
| GBT | 87–110, since it converts (a, b, l) to digits by exact division on every access | 2,976 B index |
| Tiled | 12 | No index, but 44,488 padding slots (44,860 slots for 372 records) |

## Attribution

**Layout (under LRU and under Belady).**
- **Dense axial** is best or tied on neighbourhood and zoom, where its lines are 97% utilised.
- **Morton** is best or tied on visibility, pan, gbt_hostile and thrash.
- **GBT** beats axial only on pan (12 vs 20), ties on zoom, and never beats Morton. It loses on neighbourhood (2.4× axial) and visibility, and on the hostile workload as designed.
- **Tiled**, as frozen with a padded bounding box, is worst everywhere: padded tiles hold few real cells (utilisation about 0.26–0.29).
- The layout gaps **persist under Belady**. GBT neighbourhood is 150 against axial's 91 even with optimal replacement, so they are addressing effects, not policy effects.

**Policy (within each layout, against its own LRU).**
- **LFU** is much worse on scan-like neighbourhood traffic (+482 to +636 misses) and on gbt_hostile (up to +150). It is slightly better on thrash.
- **Structural** gives a small, consistent gain on hierarchical descent only: visibility −3 to −8 misses in every layout. It is neutral on zoom and pan and harmful on neighbourhood (+75 to +485) and gbt_hostile (up to +125).
- **Adaptive** (S + 4c) tracks LFU almost exactly on neighbourhood, gbt_hostile and pan: the count term dominates for leaf-heavy lines. It improves on LRU only on visibility, by no more than structural alone, and on tiled thrash. **No adaptive advantage over the LRU/LFU controls is claimed.**
- **Belady headroom** is large on thrash (24–34% fewer misses than LRU) and moderate on visibility and gbt_hostile. It is zero for axial neighbourhood and for zoom. No online policy captured the thrash headroom.

**Interaction.** Policy effects depend strongly on layout. Structural on neighbourhood costs
+75 under axial but +485 under tiled. LFU on gbt_hostile costs +4 under axial but +150
under GBT. On tiled thrash, structural and adaptive help (−84, −88) where they hurt
elsewhere. Interaction terms reach roughly −100 to +410 misses, so layout and policy
cannot be evaluated independently.

**Combined estimated cost.** Under the declared model (1 unit per address op), dense axial is
cheapest on every workload, because GBT's per-access digit conversion (about 100 ops)
outweighs any miss saving. On memory-only cost (hits + 20·misses), Morton is best on
visibility, pan, gbt_hostile and thrash, and axial on neighbourhood and zoom.

## Dispositions

| Hypothesis | Result |
|---|---|
| Exact (a, b, level) identity is preserved under all layouts | **CONFIRMED** |
| Aperture-7 digits give unique addresses and exact parent/child relations on the domain | **CONFIRMED** |
| GBT hierarchical layout improves cache behaviour over dense axial | **MIXED**: better on pan, tied on zoom, worse on neighbourhood, visibility and gbt_hostile; never better than Morton |
| Structural (subtree) weighting improves residency | **FALSIFIED as a general policy**; small confirmed gain on hierarchical descent (visibility) only |
| Adaptive weighting improves on structural or on the LRU/LFU controls | **FALSIFIED in this fixture** |
| A hybrid (axial arithmetic + Morton/hierarchical grouping + residency weighting) is better | **Not tested** (outside frozen scope) |

## Limitations (preserved, not repaired)

- One scene, one cache configuration, and one value of α. None was tuned.
- **The tiled baseline is the padded variant named in the spec.** A sparse-tile allocator would remove the padding storage but would not change which cells share a line.
- **The address cost assumes conversion from (a, b, l) on every access.** If a traversal carries slot pointers, as real tree walks usually do, address cost disappears for all layouts, and the memory-only ranking applies. GBT conversion was implemented by repeated exact division; a table-driven encoder would be cheaper.
- Workloads are synthetic and small (89–1,927 accesses). Visibility and pan differences are a few misses.
- During testing, a fixture assertion used a supposedly outside point (40,3) that is inside the domain. It was corrected before results were generated. The spec hash is unchanged from the freeze, and the results were generated exactly once.
