#!/usr/bin/env python3
# Regenerates the concept KiCad schematic and PCB files for the SPU-13 ECP5
# OSHWA evaluator board.
#
# This script currently creates a mechanical/layout concept by grafting onto the
# KiCad Arduino Nano template. It is not a manufacturable ECP5/RP2350 schematic
# generator, and its Gerbers are not fab-ready unless ERC/DRC are later made
# clean by hand.
#
# Usage:  python3 tools/gen_kicad_layout.py
# Output: hardware/pcb/spu13_ecp5_carrier.kicad_sch  (KiCad 10 format, 20250114)
#         hardware/pcb/spu13_ecp5_carrier.kicad_pcb  (KiCad 10 format, 20241229)
#         hardware/pcb/spu13_ecp5_carrier.kicad_pro  (project metadata)

import argparse
import os, math, uuid as uuid_mod, shutil

CX, CY = 150.0, 100.0
R_OUTLINE = 55.0
R_RING = 25.0
R_FIDUCIAL = 45.0

def uid():
    return str(uuid_mod.uuid4())

def hex_verts(cx, cy, r, inset=0.0):
    r -= inset
    return [(cx + r * math.cos(math.radians(i * 60 + 30)),
             cy + r * math.sin(math.radians(i * 60 + 30))) for i in range(6)]

def gen_schematic():
    """Generate a valid KiCad 10 schematic by grafting onto the template."""
    template = '/usr/share/kicad/template/Arduino_Nano/Arduino_Nano.kicad_sch'
    with open(template) as f:
        content = f.read()
    # Replace date — KiCad 10 S-expression title_block only accepts (date ...)
    content = content.replace(
        'sam. 04 avril 2015',
        '2026-07-04')
    return content

def gen_pcb():
    """Generate a valid KiCad 10 (20241229) board by grafting onto the template."""
    # Start from the Arduino Nano template (known-good format)
    template = '/usr/share/kicad/template/Arduino_Nano/Arduino_Nano.kicad_pcb'
    with open(template) as f:
        content = f.read()

    # Remove trailing close-paren
    content = content.rstrip()
    assert content.endswith(')')
    content = content[:-1]

    # Append our hexagonal outline
    for i in range(6):
        x1, y1 = hex_verts(CX, CY, R_OUTLINE)[i]
        x2, y2 = hex_verts(CX, CY, R_OUTLINE)[(i + 1) % 6]
        content += (
            f'\t(gr_line (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f})'
            f' (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))\n')

    # ECP5-85F CABGA381 at center
    content += (
        f'\t(footprint "Package_BGA:LFBGA-381_17.0x17.0mm_Layout20x20_P0.8mm" (layer "F.Cu")\n'
        f'\t\t(at {CX:.4f} {CY:.4f})\n'
        f'\t\t(descr "ECP5-85F Central Hub \\u2014 SPU-13")\n'
        f'\t\t(property "Reference" "U100" (at 0 -12 0)'
        f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
        f'\t\t(property "Value" "LFE5UM-85F" (at 0 12 0)'
        f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
        f'\t\t(uuid "{uid()}"))\n')

    # RP2350 southbridge
    content += (
        f'\t(footprint "Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP5.15x5.15mm" (layer "F.Cu")\n'
        f'\t\t(at {CX:.4f} {CY + 40.0:.4f})\n'
        f'\t\t(descr "RP2350 QFN60 Southbridge -- all debug via USB-C")\n'
        f'\t\t(property "Reference" "U200" (at 0 -6 0)'
        f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
        f'\t\t(property "Value" "RP2350" (at 0 6 0)'
        f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
        f'\t\t(uuid "{uid()}"))\n')

    # RP2350 12 MHz crystal + 18pF load caps
    content += (
        f'\t(footprint "Crystal:Crystal_SMD_3225-4pin_3.2x2.5mm" (layer "F.Cu")\n'
        f'\t\t(at {CX + 10.0:.4f} {CY + 48.0:.4f} 0)\n'
        f'\t\t(descr "12 MHz crystal for RP2350")\n'
        f'\t\t(property "Reference" "Y1" (at 0 -4 0)'
        f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
        f'\t\t(property "Value" "12MHz" (at 0 4 0)'
        f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
        f'\t\t(uuid "{uid()}"))\n')

    # BOOT + RUN buttons
    for idx, label, y_off in [(0, "BOOT", 35), (1, "RUN", 30)]:
        content += (
            f'\t(footprint "Button_Switch_THT:SW_Push_1P1T_NO_6x6mm_H5.0mm" (layer "F.Cu")\n'
            f'\t\t(at {CX + 35.0:.4f} {CY + y_off:.4f} 0)\n'
            f'\t\t(property "Reference" "SW{idx+1}" (at 0 -6 0)'
            f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
            f'\t\t(property "Value" "{label}" (at 0 6 0)'
            f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
            f'\t\t(uuid "{uid()}"))\n')

    # 4-position DIP switch for eval mode
    content += (
        f'\t(footprint "SW_DPST:SW_DIP_SPSTx04_Slide_CTS_219-4MST_1.27x7.3mm" (layer "F.Cu")\n'
        f'\t\t(at {CX - 35.0:.4f} {CY + 42.0:.4f} 0)\n'
        f'\t\t(descr "4-bit evaluation mode DIP switch")\n'
        f'\t\t(property "Reference" "SW3" (at 0 -4 0)'
        f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
        f'\t\t(property "Value" "MODE" (at 0 4 0)'
        f' (effects (font (size 1.27 1.27) (thickness 0.15))))\n'
        f'\t\t(uuid "{uid()}"))\n')

    # 12 ring-node decoupling capacitors
    for i in range(12):
        a = math.radians(i * 30)
        x = CX + R_RING * math.cos(a)
        y = CY + R_RING * math.sin(a)
        content += (
            f'\t(footprint "Capacitor_SMD:C_0402_1005Metric" (layer "F.Cu")\n'
            f'\t\t(at {x:.4f} {y:.4f} {i*30:.1f})\n'
            f'\t\t(property "Reference" "C{i+100}" (at 0 -1.5 {i*30:.1f})'
            f' (effects (font (size 0.5 0.5) (thickness 0.1))))\n'
            f'\t\t(property "Value" "100nF" (at 0 1.5 {i*30:.1f})'
            f' (effects (font (size 0.5 0.5) (thickness 0.1))))\n'
            f'\t\t(uuid "{uid()}"))\n')

    # 3 asymmetric fiducial marks
    for idx, angle in enumerate([-90, 30, 150]):
        a = math.radians(angle)
        x = CX + R_FIDUCIAL * math.cos(a)
        y = CY + R_FIDUCIAL * math.sin(a)
        content += (
            f'\t(footprint "Fiducial:Fiducial_1.5mm_Dia_2.5mm_Outer" (layer "F.Cu")\n'
            f'\t\t(at {x:.4f} {y:.4f})\n'
            f'\t\t(property "Reference" "FID{idx+10}" (at 0 -3 0)'
            f' (effects (font (size 1 1) (thickness 0.15))))\n'
            f'\t\t(property "Value" "FID" (at 0 3 0)'
            f' (effects (font (size 1 1) (thickness 0.15))))\n'
            f'\t\t(uuid "{uid()}"))\n')

    content += ')\n'
    return content

def gen_project():
    """Copy the template's valid project file and patch the name."""
    template = '/usr/share/kicad/template/Arduino_Nano/Arduino_Nano.kicad_pro'
    with open(template) as f:
        content = f.read()
    content = content.replace('"Arduino_Nano"', '"spu13_ecp5_carrier"')
    content = content.replace('"Arduino Nano', '"SPU-13 ECP5 Carrier')
    return content

def main():
    parser = argparse.ArgumentParser(
        description="Generate the SPU-13 ECP5 evaluator KiCad concept package."
    )
    parser.add_argument(
        "--export-gerbers",
        action="store_true",
        help="also export concept Gerbers for visual review; not fab-ready"
    )
    args = parser.parse_args()

    os.makedirs("hardware/pcb", exist_ok=True)

    print("[*] Generating SPU-13 ECP5 OSHWA Evaluation PCB (KiCad 10)...")
    print("    NOTE: schematic (power-tree annotations) generated separately by:")
    print("          python3 tools/gen_kicad_schematic.py")
    print("    NOTE: run with --export-gerbers for fab review outputs")

    pcb = gen_pcb()
    with open("hardware/pcb/spu13_ecp5_carrier.kicad_pcb", "w") as f:
        f.write(pcb)
        print(f"  [+] Wrote: hardware/pcb/spu13_ecp5_carrier.kicad_pcb ({len(pcb.splitlines())} lines)")

    proj = gen_project()
    with open("hardware/pcb/spu13_ecp5_carrier.kicad_pro", "w") as f:
        f.write(proj)
        print(f"  [+] Wrote: hardware/pcb/spu13_ecp5_carrier.kicad_pro")

    if args.export_gerbers:
        # Regenerate gerbers for visual review only. These are not fabrication
        # deliverables until the KiCad project has a real schematic/netlist and
        # passes ERC/DRC against the selected fab rules.
        print("  [+] Exporting evaluation Gerbers for visual review...")
        os.makedirs("build/gerbers", exist_ok=True)
        rc = os.system("kicad-cli pcb export gerbers "
                       "hardware/pcb/spu13_ecp5_carrier.kicad_pcb "
                       "-o build/gerbers/ > /dev/null 2>&1")
        if rc == 0:
            print("  [+] Evaluation Gerbers exported to build/gerbers/")
        else:
            print("  [!] Gerber export skipped (kicad-cli error)")
    else:
        print("  [=] Skipped Gerber export. Use --export-gerbers for visual-review outputs.")

    print("[*] Done. Schematic: python3 tools/gen_kicad_schematic.py")
    print("          PCB:      {}".format("hardware/pcb/spu13_ecp5_carrier.kicad_pcb"))
    print("          Project:  kicad hardware/pcb/spu13_ecp5_carrier.kicad_pro")

if __name__ == "__main__":
    main()
