#!/usr/bin/env python3
"""
generate_openems_coupon.py
OpenEMS EM simulation for microstrip coupons.

Generates a 50-ohm microstrip trace coupon with optional via stitching.
Computes S-parameters (return loss S11, insertion loss S21) via FDTD.

Requirements:
  - openEMS with Python bindings (openems.py): https://github.com/thliebig/openEMS
  - Installation (Ubuntu/Debian):
      sudo apt-get install octave octave-dev
      git clone https://github.com/thliebig/openEMS.git
      cd openEMS && ./build.sh
      export PYTHONPATH="$PYTHONPATH:$(pwd)/python"
  - Or via conda: conda install -c thliebig openems

Stackup:
  - Substrate: FR-4 (ε_r ≈ 4.3, tan_δ ≈ 0.025 @ 1 GHz)
  - Height: 1.6 mm
  - Trace: top copper layer (35 µm)
  - Return: solid bottom copper plane
  - Via stitching: optional ground stitches along edges

Usage:
  python3 generate_openems_coupon.py --length 50 --trace-w 2.8 --out sim/coupon_50mm

Output files:
  - coupon_50mm.py — MATLAB/Octave script (if you need to review/modify)
  - coupon_50mm_s11.txt — S11 magnitude (dB) vs freq (Hz)
  - coupon_50mm_s21.txt — S21 magnitude (dB) vs freq (Hz)
  - coupon_50mm_z_in.txt — Input impedance (real, imag) vs freq (Hz)

"""

import argparse
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Try to import openEMS; if not available, fall back to script generation
try:
    from openEMS import openEMS, Port, Simulate
    HAS_OPENEMS = True
except ImportError:
    HAS_OPENEMS = False


def generate_coupon_simulation(params):
    """
    Generate an openEMS microstrip coupon simulation.

    Args:
        params: namespace with:
          - length: trace length (mm)
          - trace_w: trace width (mm)
          - substrate_h: substrate height (mm)
          - freq_min: min frequency (Hz)
          - freq_max: max frequency (Hz)
          - freq_points: number of frequency points
          - via_stitch: bool, add ground vias
          - via_pitch: via spacing (mm)
          - out_prefix: output file prefix

    Returns:
        dict with S-parameters or None if openEMS not available
    """

    # Physical parameters (FR-4)
    eps_r = 4.3
    tan_delta = 0.025
    substrate_h = params.substrate_h  # 1.6 mm
    trace_w = params.trace_w  # mm, adjust for 50 ohm
    trace_len = params.length
    via_dia = 0.8  # mm
    via_drill = 0.4  # mm

    # Frequency sweep
    f_start = params.freq_min
    f_stop = params.freq_max
    n_freqs = params.freq_points

    if not HAS_OPENEMS:
        print("openEMS not found. Generating reference script instead...")
        return generate_reference_script(params)

    try:
        # Create FDTD simulation
        FDTD = openEMS()

        # Set simulation parameters
        FDTD.SetGaussExcite((f_start + f_stop) / 2, (f_stop - f_start) / 2)
        FDTD.SetBoundaryCond([1, 1, 1, 1, 1, 1])  # PML on all sides

        # Mesh resolution (adaptive)
        max_res = 0.2  # mm (fine for 50 ohm line)
        FDTD.Set_Mesh_Resolution(max_res)

        # Create substrate
        substrate = FDTD.CreateMaterial('substrate', eps_r=eps_r, kappa=tan_delta * 2 * np.pi * 1e9 * 8.854e-12)

        # Ground plane (bottom)
        FDTD.AddBox('ground', 'PEC', priority=10,
                    start=[-50, -50, -substrate_h],
                    stop=[50, 50, -substrate_h + 0.035])

        # Substrate
        FDTD.AddBox('sub', 'substrate', priority=1,
                    start=[-50, -50, -substrate_h],
                    stop=[50, 50, 0])

        # Microstrip trace
        trace_start = -trace_len / 2
        trace_stop = trace_len / 2
        FDTD.AddBox('trace', 'PEC', priority=20,
                    start=[trace_start, -trace_w/2, -0.035],
                    stop=[trace_stop, trace_w/2, 0])

        # Port 1 (input)
        port1 = Port(FDTD, 'port1', start=[trace_start - 2, 0, -substrate_h/2],
                     stop=[trace_start, 0, 0], direction='x', z0=50)
        FDTD.AddPort(port1)

        # Port 2 (output)
        port2 = Port(FDTD, 'port2', start=[trace_stop, 0, -substrate_h/2],
                     stop=[trace_stop + 2, 0, 0], direction='x', z0=50)
        FDTD.AddPort(port2)

        # Optional via stitching
        if params.via_stitch:
            via_pitch = params.via_pitch
            x = trace_start - 5
            while x <= trace_stop + 5:
                # Via pair on either side of trace
                for y_offset in [5, -5]:
                    FDTD.AddCylinder('via_{:.1f}_{:.1f}'.format(x, y_offset), 'PEC', priority=15,
                                    start=[x, y_offset, -substrate_h], stop=[x, y_offset, 0],
                                    radius=via_dia/2, resolution=via_drill)
                x += via_pitch

        # Run simulation
        print(f"Running FDTD simulation ({f_start/1e6:.0f}–{f_stop/1e6:.0f} MHz, {n_freqs} points)...")
        Simulate(FDTD, f_start, f_stop, n_freqs)

        # Extract S-parameters
        freqs = np.linspace(f_start, f_stop, n_freqs)
        s11 = np.array([port1.GetS11(f) for f in freqs])
        s21 = np.array([port2.GetS21(f) for f in freqs])
        z_in = port1.GetImpedance(freqs)

        return {
            'freqs': freqs,
            's11': s11,
            's21': s21,
            'z_in': z_in,
            'trace_w': trace_w,
            'trace_len': trace_len,
            'substrate_h': substrate_h,
        }

    except Exception as e:
        print(f"Error during simulation: {e}")
        print("Falling back to reference script generation...")
        return generate_reference_script(params)


def generate_reference_script(params):
    """Generate a MATLAB/Octave script as reference if openEMS not available."""
    script = f"""% OpenEMS microstrip coupon simulation
% Generated reference script (run in Octave with openEMS loaded)

clear all; close all;

% Setup
Simulation_Tag = 'coupon_{params.length:.0f}mm';
physical_constants;

% Frequency sweep
f_start = {params.freq_min/1e6:.1f}e6;  % MHz
f_stop = {params.freq_max/1e6:.1f}e6;   % MHz
n_freqs = {params.freq_points};

% Geometry (mm)
trace_len = {params.length};
trace_w = {params.trace_w};
substrate_h = {params.substrate_h};

% Create FDTD
FDTD = InitFDTD();
FDTD = SetGaussExcite(FDTD, (f_start+f_stop)/2, (f_stop-f_start)/2);
FDTD = SetBoundaryCond(FDTD, [1 1 1 1 1 1]);

% Mesh
CSX = InitCSX();
mesh.x = [-50:0.2:50] * 1e-3;  % m
mesh.y = [-25:0.2:25] * 1e-3;
mesh.z = [-2:0.1:1] * 1e-3;
CSX = DefineRectGrid(CSX, 1e-3, mesh);

% Material: substrate (FR-4, eps_r=4.3, tan_delta=0.025)
CSX = AddMaterial(CSX, 'substrate');
CSX = SetMaterialProperty(CSX, 'substrate', 'Epsilon', 4.3);

% Boxes
CSX = AddBox(CSX, 'ground', 1, [-50 -50 -1.6]*1e-3, [50 50 -1.6+0.035]*1e-3);
CSX = AddBox(CSX, 'sub', 2, [-50 -50 -1.6]*1e-3, [50 50 0]*1e-3);
CSX = AddBox(CSX, 'trace', 3, [-trace_len/2 -trace_w/2 -0.035]*1e-3, [trace_len/2 trace_w/2 0]*1e-3);

% Ports (WaveGuide)
port_start_x = -trace_len/2 - 2;
port_stop_x = -trace_len/2;
port_start_z = -substrate_h/2;
port_stop_z = 0;

CSX = AddWaveGuidePort(CSX, 0, 1, 'port1', [port_start_x port_stop_x]*1e-3, ...
                       [-trace_w/2 trace_w/2]*1e-3, [port_start_z port_stop_z]*1e-3, 50);

port_start_x = trace_len/2;
port_stop_x = trace_len/2 + 2;
CSX = AddWaveGuidePort(CSX, 0, 2, 'port2', [port_start_x port_stop_x]*1e-3, ...
                       [-trace_w/2 trace_w/2]*1e-3, [port_start_z port_stop_z]*1e-3, 50);

% Write and simulate
WriteOpenEMS('openEMS.xml', CSX);
RunOpenEMS('openEMS.xml', 'openEMS.sh');

% Extract S-parameters
freqs = linspace(f_start, f_stop, n_freqs);
[s11, s21] = GetSparameters('port1', 'port2', freqs);

s11_db = 20*log10(abs(s11));
s21_db = 20*log10(abs(s21));

save([Simulation_Tag '_s11.txt'], 's11_db', '-ascii');
save([Simulation_Tag '_s21.txt'], 's21_db', '-ascii');

% Plot
figure(1);
subplot(2,1,1); plot(freqs/1e9, s11_db); ylabel('S11 (dB)'); grid on; title('Return Loss');
subplot(2,1,2); plot(freqs/1e9, s21_db); ylabel('S21 (dB)'); xlabel('Frequency (GHz)'); grid on; title('Insertion Loss');
savefig([Simulation_Tag '_sparameters.png']);

"""
    out_file = f"{params.out_prefix}_reference.m"
    os.makedirs(os.path.dirname(params.out_prefix) or '.', exist_ok=True)
    with open(out_file, 'w') as f:
        f.write(script)
    print(f"Wrote reference script: {out_file}")
    return None


def plot_results(results, params):
    """Plot S-parameters and save figures."""
    if results is None:
        print("No simulation results to plot.")
        return

    freqs = results['freqs'] / 1e9  # Convert to GHz
    s11_mag = np.abs(results['s11'])
    s21_mag = np.abs(results['s21'])
    s11_db = 20 * np.log10(np.maximum(s11_mag, 1e-6))
    s21_db = 20 * np.log10(np.maximum(s21_mag, 1e-6))
    z_in = results['z_in']
    z_in_real = np.real(z_in)
    z_in_imag = np.imag(z_in)

    # Save data
    out_prefix = params.out_prefix
    np.savetxt(f'{out_prefix}_s11.txt', np.column_stack([freqs, s11_db]), header='Freq(GHz) S11(dB)')
    np.savetxt(f'{out_prefix}_s21.txt', np.column_stack([freqs, s21_db]), header='Freq(GHz) S21(dB)')
    np.savetxt(f'{out_prefix}_z_in.txt', np.column_stack([freqs, z_in_real, z_in_imag]), header='Freq(GHz) Re(Z) Im(Z)')

    # Plot
    fig, axes = plt.subplots(3, 1, figsize=(10, 10))

    axes[0].plot(freqs, s11_db, 'b-', linewidth=2, label='S11')
    axes[0].axhline(-10, color='r', linestyle='--', label='-10 dB (VSWR ~2)')
    axes[0].set_ylabel('S11 (dB)', fontsize=12)
    axes[0].set_title(f'Microstrip Coupon: L={results["trace_len"]:.1f}mm, W={results["trace_w"]:.2f}mm', fontsize=12)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(freqs, s21_db, 'g-', linewidth=2, label='S21')
    axes[1].set_ylabel('S21 (dB)', fontsize=12)
    axes[1].set_xlabel('Frequency (GHz)', fontsize=12)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    axes[2].plot(freqs, z_in_real, 'b-', linewidth=2, label='Re(Z)')
    axes[2].plot(freqs, z_in_imag, 'r-', linewidth=2, label='Im(Z)')
    axes[2].axhline(50, color='k', linestyle='--', alpha=0.5, label='50 Ω')
    axes[2].set_ylabel('Impedance (Ω)', fontsize=12)
    axes[2].set_xlabel('Frequency (GHz)', fontsize=12)
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()

    plt.tight_layout()
    plt.savefig(f'{out_prefix}_sparameters.png', dpi=150)
    print(f"Saved plot: {out_prefix}_sparameters.png")


def parse_args():
    p = argparse.ArgumentParser(description='OpenEMS microstrip coupon S-parameter simulation')
    p.add_argument('--length', type=float, default=50.0, help='Trace length (mm)')
    p.add_argument('--trace-w', type=float, dest='trace_w', default=2.8, help='Trace width (mm) for 50 ohm')
    p.add_argument('--substrate-h', type=float, dest='substrate_h', default=1.6, help='Substrate height (mm) — FR-4')
    p.add_argument('--freq-min', type=float, dest='freq_min', default=100e6, help='Min frequency (Hz, default 100 MHz)')
    p.add_argument('--freq-max', type=float, dest='freq_max', default=10e9, help='Max frequency (Hz, default 10 GHz)')
    p.add_argument('--freq-points', type=int, dest='freq_points', default=501, help='Frequency points')
    p.add_argument('--via-stitch', action='store_true', help='Add via stitching')
    p.add_argument('--via-pitch', type=float, dest='via_pitch', default=5.0, help='Via stitch pitch (mm)')
    p.add_argument('--out', dest='out_prefix', default='coupon_sim/coupon', help='Output file prefix')
    return p.parse_args()


if __name__ == '__main__':
    params = parse_args()
    os.makedirs(os.path.dirname(params.out_prefix) or '.', exist_ok=True)

    print(f"Microstrip coupon simulation:")
    print(f"  Length: {params.length} mm")
    print(f"  Width: {params.trace_w} mm")
    print(f"  Substrate: FR-4, {params.substrate_h} mm")
    print(f"  Freq range: {params.freq_min/1e6:.1f}–{params.freq_max/1e9:.1f} GHz ({params.freq_points} points)")
    print(f"  Via stitching: {params.via_stitch}")

    results = generate_coupon_simulation(params)

    if results:
        plot_results(results, params)
        print("Simulation complete.")
    else:
        print("Reference script generated (openEMS not available).")
