# GPU evaluation profile audit Q0

**Audit date:** 2026-10-04
**Profile:** T1d legacy two-triangle prepared scene
**Status:** Q0 audit and mandatory repository closeout gates complete; S1 remains next.

## Scope and source identity

This audit follows the [GPU evaluation roadmap](GPU_EVALUATION_ROADMAP_2026-10-03.md)
and [Q0 contract](contract_gpu_evaluation_profile_audit_q0_2026-10-03.md). It
selected the existing T1d packet as a software-pilot starting point; it does
not establish hardware support for a new input format.

The repository HEAD was `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`. The
working tree was already dirty, including GPU RTL and board files. The audit
therefore binds the exact inspected bytes with
[`profile_inventory_01.json`](../build/gpu_evaluation/q0_profile_audit_20261004/profile_inventory_01.json),
which contains SHA-256 values for the fixture, references, RTL, host tools,
board configuration, roadmap, and contract. No tracked source or fixture was
changed. The read-only `python3 tools/doc_audit.py --json` command exited 0;
its full output is preserved in
[`doc_audit_01.json`](../build/gpu_evaluation/q0_profile_audit_20261004/doc_audit_01.json).

No UART, JTAG, bitstream load, wiring, reset, power, synthesis, or RTL simulation
operation was performed for Q0.

## Selected packet and fields

The fixture is 64 bytes: `A5` followed by exactly 63 payload bytes. `A5` starts
the fixed-length packet; the profile and byte count are compile-time choices,
not fields in the packet. T1d uses `SCENE_BITS=504`, two 252-bit records, and
does not enable the four-primitive, scalar, UV, or material extensions.

The loader shifts each payload byte into the high end while shifting the scene
right, so payload byte *i* ends in `scene[8*i +: 8]`. Fields occupy increasing
bit positions and are interpreted least-significant-bit first within this
packed integer. Each record is 252 bits (31.5 bytes); record 1 begins halfway
through a byte. The record map is:

| Bits in each record | Field | Interpretation |
|---|---|---|
| 15:0, 31:16, 63:32 | `a0`, `b0`, `c0` | signed 16, signed 16, signed 32 |
| 79:64, 95:80, 127:96 | `a1`, `b1`, `c1` | signed 16, signed 16, signed 32 |
| 143:128, 159:144, 191:160 | `a2`, `b2`, `c2` | signed 16, signed 16, signed 32 |
| 195:192, 199:196, 203:200 | `r`, `g`, `b` | unsigned 4-bit channels |
| 219:204, 235:220, 251:236 | `z0`, `z1`, `z2` | unsigned 16-bit depth samples |

The two fixture records use colors red `(15,0,0)` and green `(0,15,0)` and
each has `D=c0+c1+c2=257600`. The decoder map is centralized in
[`spu_scene_unpack.v`](../hardware/rtl/gpu/spu_scene_unpack.v#L21-L48); profile
selection is in [`spu_scene_profile_unpack.v`](../hardware/rtl/gpu/spu_scene_profile_unpack.v#L65-L80).

## Geometry, coverage, and depth semantics

The packet contains edge coefficients, not vertices. The board scene documents
its conversion formula as `A=yj-yi`, `B=xi-xj`, `C=-(A*xi+B*yi)` for directed
edges `V0→V1`, `V1→V2`, and `V2→V0`; the chosen screen-coordinate orientation
makes the triangle interior non-negative for every edge. The implied input
vertices are integer active-pixel coordinates. The reusable packet field
limits are signed 16-bit `a,b`, signed 32-bit `c`, four-bit RGB, and unsigned
16-bit `z`. The loader does not validate those fields or check edge consistency.

For each active pixel the rasterizer tests integer coordinates `x=0..639`,
`y=0..479`; there is no half-pixel offset. Coverage is the conjunction of three
`f>=0` tests. Each edge accumulator is signed 32-bit two's-complement and wraps
on overflow; there is no saturation. Edges are closed: a zero-valued edge is
inside, so adjacent triangles may both cover a shared edge. No top-left or
half-open ownership rule exists in this profile. To avoid wrap changing a
geometric result, the S1 validator should bound each edge's values at the active
rectangle corners to signed 32-bit range, or explicitly model modulo-2³²
coverage. The direct coverage oracle wraps to 32 bits but assumes already
prepared packet coefficients.

There is a real edge-convention mismatch to handle in the encoder. The raster
packet uses the formula above and requires non-negative interiors. In contrast,
[`gpu_depth_v2_oracle.py`](../software/lib/gpu_depth_v2_oracle.py#L44-L76)
defines `edge_coeffs(p,q)` with the opposite sign and orders `triangle_edges`
as edges opposite canonical vertices 0, 1, 2. For canonical vertices
`(V0,V1,V2)`, the T1d packet edge slots are `(V0→V1,V1→V2,V2→V0)`, with
opposite vertices `(V2,V0,V1)`. Thus a packet assembled from the oracle's edge
tuple needs the explicit mapping `packet_e0=-oracle_e2`,
`packet_e1=-oracle_e0`, `packet_e2=-oracle_e1`; packet depths must be paired as
`(zV2,zV0,zV1)`. A direct copy of the oracle tuples would invert coverage and
misassociate depths. Do not change either historical oracle or packet to hide
this discrepancy. The smallest correction is to make this transform explicit
in the S1 contract and test it independently.

Zero-area input is not rejected by the loader. The reciprocal core returns a
degenerate result for `D=0`, which makes the setup coefficients zero; no error
or invalid-scene signal is propagated to the host. The compiler must reject
collinear triangles and any input whose encoded values or active-pixel edge
range exceed the declared profile.

Depth is affine interpolation from edge functions: `D=c0+c1+c2`, with
`A_z`, `B_z`, `C_z` formed from the signed coefficient/depth dot products and
one reciprocal of `abs(D)`. A smaller signed 56-bit accumulated depth wins;
equal **post-approximation, post-shift** depths select primitive 0. There is no
clamp or saturation. The accumulator is 56-bit signed two's-complement and the
readout uses an arithmetic right shift by `frac_bits`.

The reciprocal is not exact. The denominator is normalized to a 16-bit
mantissa; a right shift discards low denominator bits. The 256-entry Q15 LUT
and one Newton–Raphson step then use finite-width products and slices; the
exponent restores scale. For the fixture `D=257600`, normalization shifts
right by two bits (the discarded bits happen to be zero). Other supported
geometry can have nonzero discarded bits, so exact rational depth and device
winner decisions must be reported separately. The RTL widths and operations
are in [`spu_depth_math.v`](../hardware/rtl/gpu/spu_depth_math.v#L66-L178),
[`spu_reciprocal_core.v`](../hardware/rtl/gpu/spu_reciprocal_core.v#L71-L140),
and [`spu_attr_stepper.v`](../hardware/rtl/gpu/spu_attr_stepper.v#L40-L63).

The vertex-to-depth association is easy to misread: in the T1d board example,
wire `z0` is the depth at `V2`, `z1` at `V0`, and `z2` at `V1`, matching the
opposite vertices of wire edges 0, 1, and 2. The same ordering appears in the
frozen fixture. `spu_depth_v2_oracle.py` uses conventional vertex order instead;
the mapping above is required at packet emission.

## Loader lifecycle and outputs

The T1d loader accepts `A5` only while idle and with no scene commit pending,
then consumes exactly 63 following valid bytes. It does not resynchronize on
another `A5` during a payload and has no incomplete-packet timeout. An
incomplete packet remains in receive state, so later bytes continue filling
it. Once the payload is complete, bytes are ignored while the candidate waits
to activate. In this T1d configuration there are no final-byte or field-window
validators; every complete payload can become pending.

The candidate is prepared through the shared depth dispatcher. Activation
waits until both triangle depth results match the current candidate generation
and a frame-start boundary occurs; then the raw scene bank and prepared depth
state switch together. Reset clears both banks and preparation state. The
loader has no host acknowledgment for start accepted, payload complete,
rejected, or active; a successful serial write and `tcdrain` establish only
host-side transmission. The governing state is in
[`spu_scene_loader.v`](../hardware/rtl/gpu/spu_scene_loader.v#L35-L123) and
[`spu_prepared_scene_control.v`](../hardware/rtl/gpu/spu_prepared_scene_control.v#L23-L80).

Internal output is RGB444, with `hal_vga` blanking RGB outside active video.
The Wukong T1d board top exports only bit 3 of each channel, so physical RGB is
one bit per channel; this packet produces red, green, and black only. The
640×480 timing counters use 800×525 totals. T1d uses the unregistered winner
output path and delays sync/active by one pixel cycle to align the pixel path.
The six-point T1e simulation samples the internal VGA consumer; it does not
qualify physical connector timing or captured monitor pixels.

## References, user path, and evidence limits

`gpu_raster_oracle.py` is a useful independent coverage calculation over
precomputed edges and models signed 32-bit wrap. `gpu_depth_v2_oracle.py`
provides an ideal `Fraction` depth reference plus a scoped reciprocal/depth
model. It does not model the whole loader, activation, scan timing, or clocked
dispatch. Its raster coverage accepts either all non-negative or all
non-positive edge signs, unlike the hardware's all-non-negative test. Its
Python depth scan also does not wrap the 56-bit accumulator and truncates
negative values toward zero where RTL `>>>` sign-extends; valid non-negative
depth cases avoid that signed corner, but it must not be presented as a complete
RTL model. The teaching programs under `software/graphics/` hard-code separate
64×32 examples; the README's commands print ASCII and do not load/edit T1d
packets or produce an image file.

Available commands and their scope:

| Command | Dependencies and output | Limitation |
|---|---|---|
| `python3 software/graphics/conventional_cpu/conventional_rasterizer.py` | Python standard library; prints a hard-coded 64×32 ASCII triangle | Floating-point control example; no T1d input or depth-v2 parity |
| `python3 software/graphics/rational_cpu/rational_rasterizer.py` | Python standard library `fractions`; prints a hard-coded 64×32 ASCII triangle | Exact edge signs for its example, but no T1d loader or depth |
| `python3 software/graphics/spu_hardware_sim/spu_streaming_rasterizer.py` | Python standard library; prints a hard-coded 64×32 ASCII triangle | No fixture input, scene lifecycle, depth path, or 32-bit wrap in this script |
| `python3 software/tests/test_gpu_t1e_prepared_scene_oracle.py` | Python standard library plus Icarus Verilog `iverilog`/`vvp`; emits six pixel results and PASS/FAIL; generated simulation files are temporary | RTL simulation, not a CPU preview or physical test; checks six coordinates only |
| `python3 tools/send_gpu_t1d_scene.py --port <serial-device> --transcript <path>` | Python standard library and a serial device; writes a transcript JSON | Hardware operation; not used in Q0 and provides no FPGA acceptance acknowledgment |

There is no current software-only command that accepts editable triangle
vertices, compiles a T1d packet, previews the resulting two-triangle image, and
saves a reproducible experiment. Users currently edit constants inside the
teaching scripts or provide an already-packed binary fixture to the RTL test.
S1 should add a small scene file and compiler/preview CLI with explicit
validation, packet hash, reference image, and inspectable coverage/depth
decisions. Keep the compiler's edge/slot transform separate from the
independent exact reference.

The six frozen fixture observations are: background `(10,10)`, triangle 0 only
`(100,300)`, triangle 1 only `(540,300)`, triangle 0 nearer `(200,100)`,
triangle 1 nearer `(400,100)`, and equal depth with triangle 0 selected
`(320,100)`. The T1e testbench checks these pixels through RTL after a complete
frame. S1 acceptance should add: a changed vertex that changes both packet and
coverage; overlap cases where each triangle wins; a tie after the device depth
quantization; pre-encode rejection of a degenerate/out-of-range scene; and an
approximation-sensitive denominator with discarded low bits nonzero. The exact
reference should derive decisions from vertices independently; the finite-width
device model should report any divergence.

Historical evidence records a T1d visual-only PASS for the frozen diagnostic
bitstream and packet: the operator saw the expected image after initial and
warm-reset transactions. No raw camera pixels or exact physical correspondence
were retained; it does not prove packet acceptance, loader activation, or
arbitrary scene support. More recent VGAFIX display evidence remains visual
HOLD, and the October 2 CRC load ended with a startup anomaly; current active
configuration is UNKNOWN. These scopes are recorded in
[`hardware_evidence.md`](../docs/hardware_evidence.md#334--vgafix-crc-delivery-transfer-complete-subsequent-startup-anomaly-2026-10-02).
The historical T1d observation is in the same ledger under the 2026-09-21
visual-only entry. No current display or hardware acceptance is inferred.

## Q0 closeout

The existing two-triangle T1d packet is a viable software-pilot seed after the
S1 contract explicitly freezes the vertex-to-wire edge transform, winding,
range checks, zero-area rejection, and finite-width depth-vs-ideal reporting.
No RTL discrepancy requires a Q0 hardware change. The audit identified no
complete software scene compiler or preview, so S1 must implement those as a
separate, testable software layer. The evidence inventory is bound by the
machine-readable SHA-256 manifest linked above.

Q0 documentation checks: `git diff --check -- spu_strategy` exited 0 for
tracked files. A separate whitespace scan found no trailing whitespace in this
untracked report, and manual relative-target inspection found all 13 report
links point to existing files. `python3 tools/doc_audit.py --check links`
exited 0 and listed 24 broken-link matches in the tracked documentation set;
the output names each location in
[`doc_links_01.log`](../build/gpu_evaluation/q0_profile_audit_20261004/doc_links_01.log).
The tool describes its results as regex hits requiring human judgement. The
untracked report is not part of that scan.

Root gate outcomes for this dirty-tree snapshot are recorded under
[`build/gpu_evaluation/q0_profile_audit_20261004/`](../build/gpu_evaluation/q0_profile_audit_20261004/):

| Gate | Result |
|---|---|
| `bash tools/verify_repo.sh` | COMPLETE, exit 0; 238 pass, 0 fail; 905 seconds |
| ROTC VM/RTL trace | PASS; 336 checks |
| IROTC VM trace | PASS; 9 tests, 0 fail |
| Rational robotics | PASS; 104 checks |
| Rational SOM | PASS; 24 checks |
| Lucas MAC oracle | PASS; 166,666 identity macros and 999,996 primitive operations |
| Padé batch inversion | PASS; 25 checks |
| Artix-7 100T Padé synthesis | COMPLETE, exit 0; `clk_fast` 39.86 MHz and input clock 307.41 MHz, both PASS at 25 MHz |

The full verifier includes the repository GPU raster/depth/top integration
tests. The scoped `TB_FILTER` testbench gate was not run because Q0 makes no
RTL change and its contract limits this audit to source/evidence review.
Synthesis evidence is in
[`a7_pade_synth_01`](../build/gpu_evaluation/q0_profile_audit_20261004/a7_pade_synth_01/);
it built the separate Padé target and was not programmed. These repository
gates do not establish GPU silicon or display acceptance.
