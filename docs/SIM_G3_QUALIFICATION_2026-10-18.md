# SIM-G3 qualification attempt — 2026-10-18

**Disposition:** INCOMPLETE — harness closeout failure

**Execution authorization:** One bounded replay attempt; no retry authorized

**Evidence directory:** `build/sim_g3/qualification_20261018_01/`

## Results

The replay command completed successfully in 25.76 seconds. Both scenes passed
the packet and RGB8 comparisons:

| Scene | Packet bytes | Packet SHA-256 | RGB8 bytes | RGB8 SHA-256 | SG-0 depth differences |
|---|---:|---|---:|---|---:|
| `identity` | 64 | `35a976682ecfbbf17684e6738cf463f7462841ef995b852fe5ff4140674beeaf` | 921,600 | `d408eec2cd55285f3c5f11f576d3f009c0799501a607cca58fbfc6f3360e70c4` | 19,845 |
| `rational_rotation` | 64 | `c05801cc609499e6da33b28e420c7c198aa8c17a95a31375a2f3955059f533b7` | 921,600 | `fe481871ffefa93f533628abde477c2c0db8f8b4c21beef685b4744f6f35ac03` | 19,878 |

The two packet files matched the frozen SG-0 packet bytes. Each raw C++ RGB8
frame matched the RGB payload from both SG-0's ideal PPM and finite-width device
PPM. The depth counts above are preserved SG-0 measurements; the C++ renderer
does not expose per-pixel depth, so this result makes no C++ depth-equivalence
claim. No FPGA output was involved.

## Closeout failure

The separately required read-only verifier command was:

```bash
timeout 60s python3 -m research.sim_g3 verify build/sim_g3/qualification_20261018_01
```

It exited 1 with `staged SG-0 reference manifest differs`. The replay staged all
members listed by the SG-0 manifest but omitted the root `manifest.json` itself;
the verifier requires that staged file. This is a harness packaging defect, not
a packet or framebuffer mismatch.

The verifier attempt is preserved in
`build/sim_g3/qualification_20261018_01/verify_attempt.json` (SHA-256
`b3b78e0168585eba984a9c5cc35acd4c221124e19d251a45b1489760555cced5`). The
successful run record remains unchanged at SHA-256
`185a0388c2617f224bf7739744a55ba0a1099c5b7086727b33f1ef50370e25a1`.

**Overall SIM-G3 qualification remains INCOMPLETE.** The packet and framebuffer
conformance results are recorded, but acceptance requires the verifier to pass.
The frozen contract forbids retries under this allocation. Any verifier repair
and follow-up verification require reviewed harness changes and renewed owner
authorization. SG-0 and SIM-G2A sources, executables, renderer semantics, ISA,
RTL and FPGA flows were not modified.
