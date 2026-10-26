#!/usr/bin/env python3
"""
generate_kicad_coupon.py
Standalone KiCad .kicad_pcb generator for a 50-ohm microstrip/TDR/PDN coupon.
Creates a simple rectangular coupon with two connector pads, a single 50-ohm
microstrip trace of configurable length, and optional via stitching.

This is a portable generator that writes a .kicad_pcb file (KiCad 6+ text format
with mm coordinates). It does not require KiCad to be installed — open the
output in KiCad to view or refine.

Usage:
  python3 generate_kicad_coupon.py --out coupon.kicad_pcb --length 50 --width 10

Defaults tuned for FR-4 microstrip on 1.6 mm stackup; use EM tools for exact
width calculation for your stackup and frequency.

Not a production template: intended as a starting point/test coupon scaffold.
"""

import argparse
import math
import os

TEMPLATE_HEADER = """
(kicad_pcb (version 20211014)
  (general
    (thickness 1.6)
    (drawings 4)
    (tracks 128)
    (zones 4)
    (modules 2)
  )
  (page A4)
  (setup
    (last_trace_width 0.25)
    (trace_clearance 0.2)
    (zone_clearance 0.5)
    (zone_45_only no)
    (trace_min 0.15)
    (via_size 0.8)
    (via_drill 0.4)
  )
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user)
    (33 "F.Adhes" user)
    (36 "Edge.Cuts" user)
  )
  (net 0 "")
  (net_class default 0.2 0.2 0.2)
"""

MODULE_TEMPLATE = """
  (module {name} (layer F.Cu) (tedit 0)
    (fp_text reference {ref} (at {xref} {yref}) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))
    (fp_text value {value} (at {xref} {yref_dy}) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))
    (pad 1 smd rect (at {pad1_x} {pad_y}) (size {pad_w} {pad_h}) (layers F.Cu F.Paste F.Mask) (net 1 "RF"))
    (pad 2 smd rect (at {pad2_x} {pad_y}) (size {pad_w} {pad_h}) (layers F.Cu F.Paste F.Mask) (net 2 "GND"))
  )
"""

TRACK_TEMPLATE = """
  (segment (start {x1} {y}) (end {x2} {y}) (width {w}) (layer F.Cu) (net 1))
"""

VIA_TEMPLATE = """
  (via (at {x} {y}) (size {dia}) (drill {drill}) (layers F.Cu B.Cu) (net 2))
"""

EDGE_CUTS_TEMPLATE = """
  (gr_poly (pts (xy {x0} {y0}) (xy {x1} {y0}) (xy {x1} {y1}) (xy {x0} {y1})) (layer Edge.Cuts))
"""

FOOTER = """
)
"""


def mm(v):
    return f"{v:.4f}"


def build_coupon(params):
    bw = params.board_w
    bh = params.board_h
    pad_w = params.pad_w
    pad_h = params.pad_h
    pad_y = 0.0
    trace_w = params.trace_w
    trace_len = params.length
    margin = 2.0

    # Positions: left pad at x = -trace_len/2 - pad_offset, right pad at +trace_len/2 + pad_offset
    pad_offset = 3.0
    left_x = -trace_len / 2 - pad_offset
    right_x = trace_len / 2 + pad_offset
    y = 0.0

    # Board extents
    x0 = -trace_len / 2 - pad_offset - margin
    x1 = trace_len / 2 + pad_offset + margin
    y0 = - (pad_h + 8) / 2 - margin
    y1 = (pad_h + 8) / 2 + margin

    out = []
    out.append(TEMPLATE_HEADER)

    # Nets
    out.append('  (net 1 "RF")\n')
    out.append('  (net 2 "GND")\n')

    # Modules (simple two-pad footprints)
    out.append(MODULE_TEMPLATE.format(name='RF_CONN_L', ref='J1', value='RF_IN', xref=mm(left_x), yref=mm(y+3.0), yref_dy=mm(y+5.0), pad1_x=mm(left_x), pad2_x=mm(left_x+pad_w+0.5), pad_y=mm(pad_y), pad_w=mm(pad_w), pad_h=mm(pad_h)))
    out.append(MODULE_TEMPLATE.format(name='RF_CONN_R', ref='J2', value='RF_OUT', xref=mm(right_x), yref=mm(y+3.0), yref_dy=mm(y+5.0), pad1_x=mm(right_x-pad_w-0.5), pad2_x=mm(right_x), pad_y=mm(pad_y), pad_w=mm(pad_w), pad_h=mm(pad_h)))

    # Trace (single center track between pads)
    trace_x1 = left_x + pad_w / 2 + 0.8
    trace_x2 = right_x - pad_w / 2 - 0.8
    out.append(TRACK_TEMPLATE.format(x1=mm(trace_x1), x2=mm(trace_x2), y=mm(y), w=mm(trace_w)))

    # Via stitching along edges for ground (every params.via_pitch mm)
    if params.via_stitch:
        x_start = trace_x1 - 5.0
        x_end = trace_x2 + 5.0
        x = x_start
        while x <= x_end:
            out.append(VIA_TEMPLATE.format(x=mm(x), y=mm(y+3.0), dia=mm(params.via_dia), drill=mm(params.via_drill)))
            out.append(VIA_TEMPLATE.format(x=mm(x), y=mm(y-3.0), dia=mm(params.via_dia), drill=mm(params.via_drill)))
            x += params.via_pitch

    # Edge cuts
    out.append(EDGE_CUTS_TEMPLATE.format(x0=mm(x0), y0=mm(y0), x1=mm(x1), y1=mm(y1)))

    out.append(FOOTER)
    return '\n'.join(out)


def parse_args():
    p = argparse.ArgumentParser(description='Generate a simple KiCad coupon .kicad_pcb file')
    p.add_argument('--out', default='coupon.kicad_pcb', help='Output filename')
    p.add_argument('--length', type=float, default=50.0, help='Trace length (mm)')
    p.add_argument('--board-w', type=float, dest='board_w', default=30.0, help='Board width (mm)')
    p.add_argument('--board-h', type=float, dest='board_h', default=12.0, help='Board height (mm)')
    p.add_argument('--trace-w', type=float, dest='trace_w', default=2.8, help='Trace width (mm) — adjust per stackup for 50 ohm')
    p.add_argument('--pad-w', type=float, dest='pad_w', default=2.5, help='Pad width (mm)')
    p.add_argument('--pad-h', type=float, dest='pad_h', default=1.8, help='Pad height (mm)')
    p.add_argument('--via-stitch', action='store_true', help='Add via stitching along coupon edges')
    p.add_argument('--via-pitch', type=float, dest='via_pitch', default=5.0, help='Via stitch pitch (mm)')
    p.add_argument('--via-dia', type=float, dest='via_dia', default=0.8, help='Via diameter (mm)')
    p.add_argument('--via-drill', type=float, dest='via_drill', default=0.4, help='Via drill (mm)')
    return p.parse_args()


if __name__ == '__main__':
    params = parse_args()
    os.makedirs(os.path.dirname(params.out) or '.', exist_ok=True)
    pcb_text = build_coupon(params)
    with open(params.out, 'w') as f:
        f.write(pcb_text)
    print(f'Wrote {params.out} — open in KiCad to inspect and add footprints or refine.')
