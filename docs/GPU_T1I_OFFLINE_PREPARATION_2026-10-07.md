# T1I offline preparation after T1H

Date: 2026-10-07. Scope: source, fixture, oracle, and visual-discriminator
review only. No synthesis, FPGA programming, UART traffic, or analyzer capture
is authorized by this note. CPU arithmetic and normalization retain priority.

The historical next feature is T1I: two independent affine fragment
coordinates, U and V, selected by the same depth winner. The original
[T1I contract](../spu_strategy/contract_gpu_t1i_interpolated_uv_2026-09-23.md)
records simulation qualification and a failed historical full repository gate
caused by an unrelated T1D timeout. That gate is not upgraded here.

The current [runbook](GPU_BRINGUP_RUNBOOK.md) and
[hardware evidence ledger](hardware_evidence.md), §§3.37–3.38, record the
completed October T1G and T1H visual replays. **T1H H1 remains HOLD**: the
historical fringe cause is unresolved even though the October operator did
not see it. The completed replay authorizes no additional hardware operation.
The retained T1G rollback image, fixtures, and tools remain unchanged. Its
image SHA-256 is
`e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5`.

## Profile and fixture review

| Profile | Record | Payload | Complete transaction | Attribute |
|---|---:|---:|---:|---|
| T1G | 252 bits | 126 bytes | 127 bytes | Geometry, RGB, depth |
| T1H | 300 bits | 150 bytes | 151 bytes | One scalar per vertex |
| T1I | 348 bits | 174 bytes | 175 bytes | U and V per vertex |

T1I preserves each scene's original 252-bit geometry/depth record and appends
six unsigned 16-bit samples. It does not extend the T1H wire record. U/V
fields begin at bits 252/268, 284/300, and 316/332. Four records are packed
little-endian after the unchanged A5 start byte. T1I and T1H profiles are
mutually exclusive. The existing loader's payload-completion boundary is 174
payload bytes; 173 payload bytes must not commit.

[The generator](../tools/generate_gpu_t1i_uv_scenes.py) pins the legacy A/B/C
source fixture hashes before deriving T1I outputs. Scene B adds (2048,1024)
to A's coordinate table; C adds (1024,4096). Their geometry/depth comes from
the corresponding legacy B/C fixtures, so a changed image is not solely an
attribute-offset experiment. Do not regenerate or hand-edit fixtures during
this preparation.

## Independent oracle and discriminator

[The Python oracle](../software/tests/test_gpu_t1i_uv.py) decodes geometry,
depth, and vertex samples directly from fixtures. It derives reciprocal-scaled
planes through `gpu_depth_v2_oracle.full_reciprocal`, checks coverage with
three signed edge equations, and independently chooses minimum depth. Ties
retain the first lane. It consumes no RTL coefficients, accumulators, or
winner signals to compute expected U/V. Each value uses an arithmetic right
shift; uncovered output is `(valid,lane,u,v)=(0,0,0,0)`.

This is a bit-exact oracle for the frozen reciprocal and shift semantics,
not a claim of unrestricted rational interpolation. Oracle independence is
from RTL state; it shares the frozen numerical contract and Python reciprocal
oracle. The simulation harness also contains hierarchical RTL alignment and
activation assertions; those checks alone do not substitute for the Python
pixel comparison.

Original T1I provides no RGB visualization. The separate historical
`T1I_UV_DIAG` maps valid U[14] to red, V[14] to green, and blue to zero:
black, red, green, yellow. Covered black is visually indistinguishable from
uncovered black, so the oracle must retain validity and winner identity.
A/B/C need not contain all four covered colors individually.

Fresh offline results for the 80×100 oracle region are:

| Scene | Covered black/red/green/yellow | Winner lanes 0/1/2/3 | Uncovered |
|---|---|---|---:|
| A | 1499 / 504 / 438 / 0 | 773 / 742 / 488 / 438 | 5559 |
| B | 338 / 253 / 231 / 102 | 231 / 231 / 231 / 231 | 7076 |
| C | 1351 / 165 / 438 / 487 | 773 / 742 / 488 / 438 | 5559 |

A→B changes 1426 palette pixels and A→C changes 1502. These are computed
fixture expectations, not captured physical pixels or a fresh RTL test.
They provide an offline discriminator before any later visual replay is
specified. Return-A must use the same A fixture and reproduce the A oracle
tuple map.

Historical physical classifications remain separate. Ledger §3.14 records
T1I diagnostic **HOLD — ghosting visible**; §3.16 records a post-winner
register **PASS (operator-observed, visual-only)** for broad A/B/C/A changes,
with a detached red artifact still unresolved. Neither entry establishes
exact physical U/V or closes T1H H1.

## Reproduce the offline fixture and oracle checks

Run from the repository root. This command reads existing sources and
fixtures and writes no fixture, build artifact, or hardware state:

```bash
python3 - <<'PY'
import hashlib
import sys
from pathlib import Path
sys.path[:0] = ['software/tests', 'tools']
from test_gpu_t1i_uv import load_scene, decode, oracle
from test_gpu_t1i_uv_uart_loader import FIXTURES
from generate_gpu_t1i_uv_scenes import SCENES, BASE_UV

patterns = []
for key in 'abc':
    name, expected_wire_sha = FIXTURES[key.upper()]
    _, scene = load_scene(name)
    wire = b'\xa5' + scene.to_bytes(174, 'little')
    assert hashlib.sha256(wire).hexdigest() == expected_wire_sha
    source_name, source_sha, explicit, offset = SCENES[key]
    raw = Path('fixtures', source_name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source_sha
    original = int.from_bytes(bytes.fromhex(raw.decode().strip())[1:], 'little')
    coords = explicit or tuple(tuple((u+offset[0], v+offset[1])
        for u, v in lane) for lane in BASE_UV)
    for lane in range(4):
        record = (scene >> (348*lane)) & ((1 << 348)-1)
        assert record & ((1 << 252)-1) == (original >> (252*lane)) & ((1 << 252)-1)
        for vertex, (u, v) in enumerate(coords[lane]):
            assert (record >> (252+32*vertex)) & 65535 == u
            assert (record >> (268+32*vertex)) & 65535 == v
    decoded = decode(scene)
    samples = [oracle(decoded, x, y) for y in range(100) for x in range(80)]
    patterns.append(samples)
    classes, lanes, uncovered = [0]*4, [0]*4, 0
    for valid, lane, u, v in samples:
        if valid:
            classes[((u >> 14) & 1)+2*((v >> 14) & 1)] += 1
            lanes[lane] += 1
        else:
            uncovered += 1
            assert (lane, u, v) == (0, 0, 0)
    print(key.upper(), 'covered_classes=', classes, 'winner_lanes=', lanes,
          'uncovered=', uncovered, 'wire_sha256=', expected_wire_sha)
def palette(sample):
    return (((sample[2] >> 14) & 1)+2*((sample[3] >> 14) & 1)) if sample[0] else 0
for index in (1, 2):
    print('A/'+'ABC'[index], 'palette_changes=',
          sum(palette(a) != palette(b) for a, b in zip(patterns[0], patterns[index])))
PY
```

No fresh RTL simulation was required for this documentation-only review.
Existing future qualification paths are `test_gpu_t1i_uv.py` (32,000 small
frame samples plus profile/activation checks), `test_gpu_t1i_uv_uart_loader.py`
(UART reconstruction and bank activation), and
`test_gpu_t1i_uv_production_timing.py` (production timing with 32,000 oracle
ROI samples, not independent oracle comparison of every 640×480 pixel).
Use the detached runner for any deterministic job expected to exceed 60
seconds; no such job is launched by this note.

Before a future hardware proposal, freeze the selected historical artifact
and its source-provenance limit, transaction length, diagnostic mapping,
oracle reference, observation criteria, rollback identities, and owner
campaign budget. That preparation does not authorize execution.
