#!/usr/bin/env python3
# pdn_analyze.py — SPU-13 ECP5 VCC_CORE PDN impedance analysis.
#
# Generates a SPICE deck, runs ngspice, parses the raw output,
# and checks against the 0.15 Ohm target.
#
# Usage:  python3 tools/pdn_analyze.py
# Deps:   ngspice (in PATH)

import subprocess, sys, os, math, re

NETLIST = r"""
* SPU13_ECP5_PDN : VCC_CORE impedance simulation
* Simulates decoupling network for ECP5-85F 1.1V rail
* Target: Z_PDN < 0.15 Ohm from 1kHz to 10MHz

* TPS62082 VRM (2MHz buck, 5mOhm output impedance)
V_VRM VCC 0 DC 1.1
R_VRM VCC VRM 5m
L_VRM VRM VRM_OUT 2nH

* Bulk MLCC: 2x 22uF 0805
C_B1 VRM_OUT BULK1 22uF
R_B1 BULK1 BULK1L 3m
L_B1 BULK1L 0 0.5nH
C_B2 VRM_OUT BULK2 22uF
R_B2 BULK2 BULK2L 3m
L_B2 BULK2L 0 0.5nH

* Mid MLCC: 2x 4.7uF 0603 (deliberate higher ESR to damp anti-resonance)
C_M1 VRM_OUT MID1 4.7uF
R_M1 MID1 MID1L 0.15
L_M1 MID1L 0 0.4nH
C_M2 VRM_OUT MID2 4.7uF
R_M2 MID2 MID2L 0.15
L_M2 MID2L 0 0.4nH

* HF MLCC: 4x 100nF 0402 (spread ESL: 3x 0.3nH, 1x 0.6nH)
C_H1 VRM_OUT H1 100nF
R_H1 H1 H1L 8m
L_H1 H1L 0 0.3nH
C_H2 VRM_OUT H2 100nF
R_H2 H2 H2L 8m
L_H2 H2L 0 0.5nH
C_H3 VRM_OUT H3 100nF
R_H3 H3 H3L 8m
L_H3 H3L 0 0.3nH
C_H4 VRM_OUT H4 100nF
R_H4 H4 H4L 8m
L_H4 H4L 0 0.6nH

* VHF MLCC: 6x 10nF 0402 (spread ESL: 3x low, 3x medium, spreads SRF)
C_V1 VRM_OUT V1 10nF
R_V1 V1 V1L 20m
L_V1 V1L 0 0.3nH
C_V2 VRM_OUT V2 10nF
R_V2 V2 V2L 20m
L_V2 V2L 0 0.5nH
C_V3 VRM_OUT V3 10nF
R_V3 V3 V3L 20m
L_V3 V3L 0 0.8nH
C_V4 VRM_OUT V4 10nF
R_V4 V4 V4L 20m
L_V4 V4L 0 0.3nH
C_V5 VRM_OUT V5 10nF
R_V5 V5 V5L 20m
L_V5 V5L 0 0.5nH
C_V6 VRM_OUT V6 10nF
R_V6 V6 V6L 20m
L_V6 V6L 0 0.8nH

* Intentional loss through mid cap ESR + ESL diversity above; no 47nF (adds resonance)
L_MH1 MH1L 0 0.3nH
C_MH2 VRM_OUT MH2 47nF
R_MH2 MH2 MH2L 12m
L_MH2 MH2L 0 0.3nH





* UHF MLCC: 2x 1nF 0402 (spread ESL)
C_U1 VRM_OUT U1 1nF
R_U1 U1 U1L 50m
L_U1 U1L 0 0.3nH
C_U2 VRM_OUT U2 1nF
R_U2 U2 U2L 50m
L_U2 U2L 0 0.6nH

* PCB plane capacitance (60x60mm, 0.2mm prepreg)
C_PCB VRM_OUT PCB 150pF
R_PCB PCB PCBL 2m
L_PCB PCBL 0 5pH

* BGA package + die
L_BGA VRM_OUT FPGA 0.05nH
C_DIE FPGA 0 50nF
R_DIE FPGA DIE 2m

* AC: inject 1A => V(FPGA) = impedance in Ohms
I_INJ FPGA 0 AC 1

.AC DEC 100 1k 100Meg
.PRINT AC V(FPGA)
.END
"""

def parse_raw_file(path):
    """Parse ngspice raw file format."""
    data = []
    with open(path, 'r') as f:
        lines = f.readlines()

    in_data = False
    for line in lines:
        line = line.strip()
        if line.startswith("Values:"):
            in_data = True
            continue
        if in_data and line and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    # ngspice raw format: index freq real imag
                    idx = int(parts[0])
                    freq = float(parts[1])
                    # Complex magnitude
                    real = float(parts[2])
                    imag = float(parts[3])
                    mag = math.sqrt(real*real + imag*imag)
                    data.append((freq, mag))
                except (ValueError, IndexError):
                    pass
    return data

def parse_print_output(text):
    """Parse ngspice .PRINT text output."""
    data = []
    for line in text.split('\n'):
        line = line.strip()
        # Skip headers and empty lines
        if not line or line.startswith('Index') or line.startswith('-') or line.startswith('Circuit') or line.startswith('Note'):
            continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                idx = int(parts[0])
                freq = float(parts[1])
                # Complex format from ngspice: "real, imag" or "val"
                real_str = parts[2].rstrip(',')
                real = float(real_str)
                if len(parts) >= 4:
                    imag_str = parts[3].rstrip(',')
                    imag = float(imag_str)
                else:
                    imag = 0.0
                mag = math.sqrt(real*real + imag*imag)
                data.append((freq, mag))
            except ValueError:
                pass
    return data

def main():
    os.makedirs("build", exist_ok=True)
    print("=" * 60)
    print("  SPU-13 ECP5 PDN Impedance Analysis")
    print("=" * 60)

    # Write clean netlist
    netlist = "/tmp/spu_pdn.cir"
    with open(netlist, 'w') as f:
        f.write(NETLIST)

    print("\n[*] Running ngspice...")
    result = subprocess.run(
        ["ngspice", "-b", netlist],
        capture_output=True, text=True, timeout=30
    )

    # Combine stdout+stderr
    all_output = result.stdout + "\n" + result.stderr

    # Check for raw output file
    raw_files = []
    for d in ["/tmp", os.getcwd()]:
        for f in os.listdir(d):
            if f.endswith(".raw"):
                raw_files.append(os.path.join(d, f))

    data = []
    if raw_files:
        raw_path = max(raw_files, key=os.path.getmtime)
        print(f"  Raw file found: {raw_path}")
        data = parse_raw_file(raw_path)

    if not data:
        data = parse_print_output(all_output)

    if not data:
        print("  [!] Could not parse ngspice output. Debug:")
        # Print last 30 lines of combined output
        for line in all_output.split('\n')[-30:]:
            if line.strip():
                print(f"    |{line}")

        # Try alternative: look for any numerical columns
        for line in all_output.split('\n'):
            if line.strip() and not line.startswith('Index') and not line.startswith('-') and not line.startswith('Circuit'):
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0].lstrip('-+').isdigit():
                    try:
                        freq = float(parts[1])
                        mag = float(parts[-1])
                        data.append((freq, mag))
                    except ValueError:
                        pass

        if not data:
            print("\n  [!] No simulation data parsed. Check ngspice installation.")
            sys.exit(1)

    print(f"\n  Parsed {len(data)} frequency points.")

    # Analyze
    TARGET_OHM = 0.15
    failures = 0
    worst_z = 0.0
    worst_f = 0.0
    worst_above_target = 0.0

    print(f"\n  {'Frequency (Hz)':>14}  {'Z (Ohm)':>10}  {'Target':>8}  {'Status':>6}")
    print(f"  {'-'*14}  {'-'*10}  {'-'*8}  {'-'*6}")

    for freq, mag in data:
        if freq < 1e3:
            continue
        target = TARGET_OHM if freq <= 10e6 else (0.5 if freq <= 50e6 else 1.0)
        ok = mag <= target
        if not ok:
            failures += 1
            excess = mag - target
            if excess > worst_above_target:
                worst_above_target = excess
        if mag > worst_z:
            worst_z = mag
            worst_f = freq

        # Print select data points
        if (freq <= 1e5 and int(freq) % 20000 == 0) or \
           (freq <= 1e6 and int(freq) % 200000 == 0) or \
           (freq <= 10e6 and int(freq) % 2000000 == 0) or \
           freq >= 50e6:
            print(f"  {freq:>14.1f}  {mag:>10.6f}  {target:>8.3f}  {'PASS' if ok else 'FAIL':>6}")

    print(f"  {'-'*14}  {'-'*10}  {'-'*8}  {'-'*6}")

    # At 1MHz specifically
    z_at_1m = None
    for f, m in data:
        if 0.9e6 <= f <= 1.1e6:
            z_at_1m = m
            break

    # Summary — use per-band target, not a single threshold
    if worst_f <= 10e6:
        band_target = TARGET_OHM
        band_name = "<=10MHz (core band)"
    elif worst_f <= 50e6:
        band_target = 0.5
        band_name = "10-50MHz (transition band)"
    else:
        band_target = 1.0
        band_name = ">50MHz (VHF)"

    # Check only the core band (<=10MHz) for PASS/FAIL
    core_failures = sum(1 for f, m in data if 1e3 <= f <= 10e6 and m > TARGET_OHM)

    print(f"\n  Summary:")
    print(f"    Worst impedance:  {worst_z:.6f} Ohm @ {worst_f:.1e} Hz")
    print(f"    Worst band:       {band_name} (target {band_target} Ohm)")
    print(f"    Z at 1 MHz:       {z_at_1m:.6f} Ohm" if z_at_1m else "    Z at 1 MHz:       N/A")
    print(f"    Core band Z<=0.15: {'PASS' if core_failures == 0 else 'FAIL'}")

    if core_failures == 0:
        print(f"\n  {chr(9632)} PASS: PDN impedance within target in core band.")
        return 0
    else:
        print(f"\n  {chr(9632)} FAIL: {core_failures} violations in core band.")
        print(f"      Mitigation: add 2-4 more 100nF 0402 caps near BGA,")
        print(f"      or reduce via inductance with closer GND returns.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
