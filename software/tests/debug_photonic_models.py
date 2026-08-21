#!/usr/bin/env python3
"""
debug_photonic_models.py — Precision debugging and Model B refinement

This script investigates why Model B (ideal optical) doesn't match Model A (exact).
Tests encoding precision, identifies numerical bottlenecks, and proposes fixes.
"""

import math
import random
from typing import Tuple


class ModelA_ExactSPU:
    """Model A: Exact SPU-13 oracle."""
    
    @staticmethod
    def smul(a: int, b: int, c: int, d: int) -> Tuple[int, int]:
        """(a + b√3)(c + d√3) = (ac + 3bd) + (ad + bc)√3"""
        a_prime = a * c + 3 * b * d
        b_prime = a * d + b * c
        
        MAX_VAL = 32767
        MIN_VAL = -32768
        a_prime = max(MIN_VAL, min(a_prime, MAX_VAL))
        b_prime = max(MIN_VAL, min(b_prime, MAX_VAL))
        
        return int(a_prime), int(b_prime)


class PrecisionDebugger:
    """Tools for measuring numerical error in optical pipeline."""
    
    @staticmethod
    def dual_rail_error_analysis():
        """
        Measure encoding/decoding error for dual-rail representation.
        
        Encoding: integer a → E_pos, E_neg → a_recovered
        """
        print("\n=== Dual-Rail Encoding Precision ===")
        scale = 0.1
        
        max_error = 0
        problematic_values = []
        
        for a in range(-100, 101):
            # Encode
            if a >= 0:
                E_pos = scale * a
                E_neg = 0.0
            else:
                E_pos = 0.0
                E_neg = scale * (-a)
            
            # Detect (E_pos - E_neg represents signed field)
            E = E_pos - E_neg
            
            # Decode
            a_recovered = int(round(E / scale))
            
            error = abs(a - a_recovered)
            if error > max_error:
                max_error = error
            
            if error > 0:
                problematic_values.append((a, a_recovered, error))
        
        print("  Scale factor: {0}".format(scale))
        print("  Max encoding error: {0}".format(max_error))
        print("  Problematic values: {0}".format(len(problematic_values)))
        
        if problematic_values:
            print("  Examples:")
            for original, recovered, error in problematic_values[:10]:
                print("    {0} → {1} (error: {2})".format(original, recovered, error))
        
        return max_error == 0
    
    @staticmethod
    def power_to_amplitude_error():
        """
        Measure error in power-to-amplitude conversion.
        
        Issue: |E|² = power, but we recover |E| via √(power).
        """
        print("\n=== Power-to-Amplitude Recovery ===")
        
        scale = 0.1
        errors = []
        
        for amplitude in [0.1, 0.5, 1.0, 5.0, 10.0]:
            power = amplitude ** 2
            recovered_amp = math.sqrt(power)
            error = abs(amplitude - recovered_amp)
            errors.append((amplitude, error))
            print("  Amp: {0:5.1f}, Power: {1:7.4f}, Recovered: {2:5.1f}, Error: {3:8.6f}".format(
                amplitude, power, recovered_amp, error))
        
        return max(e[1] for e in errors)
    
    @staticmethod
    def matrix_scaling_error():
        """
        Measure error from matrix scaling: M_norm = M / σ_max.
        
        For realistic operands, σ_max can be large, requiring high precision.
        """
        print("\n=== Matrix Scaling & Renormalization ===")
        
        test_cases = [
            (1, 1, 1, 1),         # Small: σ_max = max(1+3=4, 1+1=2, 1) = 4
            (100, 100, 100, 100), # Large: σ_max = max(100+300, 100+100, 1) = 400
            (-50, 50, 50, -50),   # Mixed signs
        ]
        
        for a, b, c, d in test_cases:
            # Expected result (Model A)
            expected_a, expected_b = ModelA_ExactSPU.smul(a, b, c, d)
            
            # Optical pipeline
            sigma_max = max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)
            
            # Normalized matrix elements
            M00 = float(c) / sigma_max
            M01 = (3.0 * float(d)) / sigma_max
            M10 = float(d) / sigma_max
            M11 = float(c) / sigma_max
            
            # Input fields (scale = 0.1)
            scale = 0.1
            E_a_in = scale * a
            E_b_in = scale * b
            
            # Scattering (simplified: no phase)
            E_a_out = M00 * E_a_in + M01 * E_b_in
            E_b_out = M10 * E_a_in + M11 * E_b_in
            
            # Measure (power)
            V_a = E_a_out ** 2
            V_b = E_b_out ** 2
            
            # Rescale and quantize
            V_a_rescaled = V_a * sigma_max
            V_b_rescaled = V_b * sigma_max
            
            recovered_a = int(round(V_a_rescaled / (scale ** 2)))
            recovered_b = int(round(V_b_rescaled / (scale ** 2)))
            
            match_a = (recovered_a == expected_a)
            match_b = (recovered_b == expected_b)
            
            print("  ({0}, {1}) × ({2}, {3})".format(a, b, c, d))
            print("    σ_max: {0}".format(sigma_max))
            print("    Expected: ({0}, {1})".format(expected_a, expected_b))
            print("    Recovered: ({0}, {1})".format(recovered_a, recovered_b))
            print("    Match: a={0}, b={1}".format(match_a, match_b))
            print()
    
    @staticmethod
    def operand_magnitude_sweep():
        """
        Measure Model B error as function of operand magnitude.
        """
        print("\n=== Error vs. Operand Magnitude ===")
        
        from test_photonic_models_smul import ModelA_ExactSPU, ModelB_IdealOptical
        
        for max_val in [1, 5, 10, 20, 50, 100]:
            matches = 0
            tests = 0
            
            random.seed(42)
            for _ in range(100):
                a, b, c, d = [random.randint(-max_val, max_val) for _ in range(4)]
                
                result_a = ModelA_ExactSPU.smul(a, b, c, d)
                result_b = ModelB_IdealOptical.smul(a, b, c, d)
                
                if result_a == result_b:
                    matches += 1
                tests += 1
            
            pct = 100.0 * matches / tests
            print("  Operands ∈ [-{0:3d}, {0:3d}]: {1:3d}/{2} ({3:5.1f}%)".format(
                max_val, matches, tests, pct))


if __name__ == "__main__":
    print("=" * 70)
    print("PHOTONIC MODEL PRECISION DEBUGGING")
    print("=" * 70)
    
    debugger = PrecisionDebugger()
    
    # Test 1: Encoding precision
    encoding_ok = debugger.dual_rail_error_analysis()
    
    # Test 2: Power-to-amplitude conversion
    power_error = debugger.power_to_amplitude_error()
    
    # Test 3: Matrix scaling pipeline
    debugger.matrix_scaling_error()
    
    # Test 4: Empirical error sweep (requires Models to be importable)
    try:
        debugger.operand_magnitude_sweep()
    except ImportError:
        print("\n(Skipping operand sweep—run in SPU directory)")
    
    print("\n" + "=" * 70)
    print("FINDINGS")
    print("=" * 70)
    print("Dual-rail encoding:      {0}".format("OK" if encoding_ok else "NEEDS WORK"))
    print("Power/amplitude recovery: {0:.6f} max error".format(power_error))
    print("\nNext: Revise scale factor and matrix representation.")
    print("=" * 70)
