"""NGW-H1 frozen specification. Fixed before any cache result was generated;
its SHA-256 is recorded in FINDINGS.md. Do not edit after results exist.

Scene
  K = 5 aperture-7 levels, root (0,0,5). A level-l cell (l >= 1) is refined
  (all 7 children exist) iff l == K or N(center - FOCUS) <= REFINE_C * 7^l,
  with N the Eisenstein norm (exact quadrance, fine-lattice units).
  Every tree node (all levels) is one 16-byte record.

Memory model (model only, no hardware claim)
  record 16 B, line 64 B = 4 records, fast tier 16 lines = 4 sets x 4 ways,
  set = line_index mod 4. Hit latency 1, miss latency 20 (cost units).
  Address computation costs 1 unit per counted primitive op.
  Estimated cost = hits*HIT + misses*MISS + address_ops*ADDR_OP.
  Transferred bytes = misses * 64. Line utilisation = distinct records touched
  during a residency / 4, averaged over all residencies (incl. those live at end).

Layouts (all dense over existing records unless stated)
  axial    sort by (level, b, a)
  morton   sort by (level, interleave(a - a_min, b - b_min)), 16 bits each, a in even bits
  gbt      preorder DFS of the tree, children in digit order 0..6
  tiled    per level, padded bounding box in (a, b), 2x2 tiles (one tile = one line),
           tiles row-major; padding slots exist but are never referenced

Policies (eviction within the target set; all ties -> least recently used)
  LRU         least recently used
  LFU         smallest in-residency hit count (count starts at 1 on fill, reset on eviction)
  structural  smallest line weight S(line) = sum over records in the line of
              subtree_size(cell) (nodes in its subtree incl. itself; padding = 0)
  adaptive    smallest S(line) + ALPHA * c(line), c = in-residency access count
  belady      line whose next use in this layout's own line stream is farthest;
              never-reused lines first; ties among them -> lowest line index

Workloads (cell-identity streams, deterministic)
  neighborhood  each leaf in (b, a) order, then its 6 same-level neighbours that exist
  zoom          for 24 points stepping from (-20,7) toward FOCUS, root-to-leaf ancestor chain
  visibility    3 views: recursive descent visiting children with N(c - V) <= VIS_C * 7^l
  pan           view disk N(c - V_t) <= PAN_Q over leaves, V_t stepping along b, 12 steps
  gbt_hostile   alternate same-level leaf neighbour pairs whose top-level digits differ, x3
  thrash        LCG-permuted cycle over all leaves, 3 passes (no locality)
"""
from __future__ import annotations

K = 5
FOCUS = (3, 1)
REFINE_C = 4
RECORD_B, LINE_B = 16, 64
PER_LINE = LINE_B // RECORD_B
SETS, WAYS = 4, 4
HIT, MISS, ADDR_OP = 1, 20, 1
ALPHA = 4
VIS_C = 2
VIEWS = [(3, 1), (-8, 4), (10, -6)]
PAN_Q = 60
PAN_START, PAN_STEP, PAN_STEPS = (-12, -6), (0, 1), 12
ZOOM_START, ZOOM_STEPS = (-20, 7), 24
LCG_A, LCG_C, LCG_M, LCG_SEED = 1103515245, 12345, 2 ** 31, 7
