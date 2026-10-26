"""gpu_raster_oracle.py -- independent Python oracle for the SPU-13 GPU
triangle rasterizer's edge-function coverage test
(hardware/rtl/gpu/spu_edge_stepper.v + spu_raster_unit.v).

Bit-exact: models the same 16-bit signed a/b, 32-bit signed c, and
32-bit signed accumulator truncation the RTL uses (spu_edge_stepper.v's
`reg signed [31:0] f`). Evaluated *directly* (f = a*x + b*y + c at each
(x,y)), not incrementally like the RTL -- an oracle that accumulated
the same way could share an incremental-accumulation bug with the RTL
it's meant to check independently.
"""


def trunc32(v: int) -> int:
    """Truncate to a 32-bit two's-complement signed value, matching
    Verilog's `reg signed [31:0]` wraparound behavior exactly."""
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


def edge_inside(a: int, b: int, c: int, x: int, y: int) -> bool:
    """One edge's inside test: A*x + B*y + C >= 0. Matches
    spu_edge_stepper.v's `inside_out = (f >= 0)` where f is the
    incrementally-accumulated value of this same expression."""
    f = trunc32(a * x + b * y + c)
    return f >= 0


def triangle_covered(edges, x: int, y: int) -> bool:
    """edges: iterable of 3 (a, b, c) tuples. Covered iff all three
    edges are inside, matching spu_raster_unit.v's
    `covered = inside0 & inside1 & inside2`."""
    return all(edge_inside(a, b, c, x, y) for (a, b, c) in edges)


def covered_pixels(edges, width: int, height: int):
    """All (x, y) in [0,width) x [0,height) with triangle_covered True.
    Returned as a set, for exhaustive-equality comparison against an
    independent RTL scan of the same triangle over the same screen."""
    return {
        (x, y)
        for y in range(height)
        for x in range(width)
        if triangle_covered(edges, x, y)
    }
