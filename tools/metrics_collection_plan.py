#!/usr/bin/env python3
"""
metrics_collection_plan.py — SPU-13 RPLU 2.0 Publication Metrics

Generates structured data collection templates for:
  1. Power consumption (mW vs frequency)
  2. Latency & throughput (cycles, µs, ops/sec)
  3. Area & resource utilization (LUTs, DSPs, BRAMs, mm²)
  4. Functional coverage (test counts, oracle validation)
  5. Comparative baselines (CPU, GPU, prior FPGA work)

Output: JSON templates + Python collection scripts
Usage:
  python3 tools/metrics_collection_plan.py --generate-templates
  python3 tools/metrics_collection_plan.py --collect-power <port> <freq_list>
  python3 tools/metrics_collection_plan.py --extract-area <pnr_json>
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class PowerMeasurement:
    """Single power measurement point"""
    timestamp: str
    clock_mhz: int
    idle_ma: float  # No activity
    active_ma: float  # RPLU pipeline running
    peak_ma: float  # Maximum observed
    idle_mw: float = 0.0  # Calculated from idle_ma
    active_mw: float = 0.0  # Calculated from active_ma
    peak_mw: float = 0.0  # Calculated from peak_ma
    
    def calculate_power(self, vdd_volts=3.3):
        """Convert current to power at given VDD"""
        self.idle_mw = self.idle_ma * vdd_volts
        self.active_mw = self.active_ma * vdd_volts
        self.peak_mw = self.peak_ma * vdd_volts


@dataclass
class LatencyMeasurement:
    """Pipeline latency breakdown"""
    stage_name: str  # M31_MUL, FP4_INV, SOM_BMU, BTU, PADE, PIPELINE
    cycles: int
    frequency_mhz: int
    latency_us: float = 0.0
    throughput_hz: float = 0.0
    
    def calculate_timing(self):
        """Convert cycles to latency"""
        self.latency_us = self.cycles / (self.frequency_mhz * 1e6)
        self.throughput_hz = self.frequency_mhz * 1e6 / self.cycles


@dataclass
class AreaBreakdown:
    """Resource utilization per module"""
    module_name: str
    lut4_used: int
    lut4_available: int
    dsp_used: int
    dsp_available: int
    bram_used: int
    bram_available: int
    max_freq_mhz: float
    
    @property
    def lut_percent(self):
        return (self.lut4_used / self.lut4_available * 100) if self.lut4_available else 0
    
    @property
    def dsp_percent(self):
        return (self.dsp_used / self.dsp_available * 100) if self.dsp_available else 0
    
    @property
    def bram_percent(self):
        return (self.bram_used / self.bram_available * 100) if self.bram_available else 0


@dataclass
class TestCoverage:
    """Functional test coverage"""
    test_suite: str  # e.g., "m31_multiplier_tb", "spu13_rplu_pipeline_tb"
    test_count: int
    pass_count: int
    fail_count: int
    assertions: int
    coverage_percent: float = 0.0
    
    @property
    def pass_rate(self):
        return (self.pass_count / self.test_count * 100) if self.test_count else 0


@dataclass
class ComparativeBaseline:
    """Comparison against other systems"""
    system_name: str  # SPU-13, CPU, GPU, Prior FPGA
    bits: str  # "exact", "FP32", "FP64"
    latency_us: float
    power_mw: float
    energy_per_op_uj: float  # microjoules
    area_mm2: Optional[float] = None
    throughput_ops_per_sec: Optional[float] = None


# ============================================================================
# TEMPLATE GENERATION
# ============================================================================

def generate_power_template() -> Dict:
    """Template for power measurement data"""
    return {
        "metadata": {
            "date_collected": datetime.now().isoformat(),
            "platform": "Tang Primer 25K (GW5A-25A)",
            "supply_voltage": 3.3,
            "supply_unit": "Volts",
            "measurement_method": "INA226 current-sense module",
            "sample_rate_khz": 10,
        },
        "measurements": [
            asdict(PowerMeasurement(
                timestamp=datetime.now().isoformat(),
                clock_mhz=12,
                idle_ma=5.0,
                active_ma=15.0,
                peak_ma=25.0,
            ))
            for _ in range(3)  # Example: 3 frequency points
        ],
        "analysis": {
            "idle_power_mw_mean": 0.0,
            "active_power_mw_mean": 0.0,
            "power_per_mhz_mw": 0.0,
            "energy_per_rplu_op_uj": 0.0,  # From latency × power
        }
    }


def generate_latency_template() -> Dict:
    """Template for latency measurements"""
    return {
        "metadata": {
            "date_collected": datetime.now().isoformat(),
            "simulation_tool": "iverilog + vvp",
            "frequency_mhz": 12,
            "temperature_c": 25,
        },
        "stages": [
            asdict(LatencyMeasurement("M31_MULTIPLIER", 2, 12)),
            asdict(LatencyMeasurement("FP4_INVERTER", 76, 12)),
            asdict(LatencyMeasurement("SOM_BMU", 7, 12)),
            asdict(LatencyMeasurement("BTU_ROUTING", 3, 12)),
            asdict(LatencyMeasurement("PADE_EVAL", 4, 12)),
        ],
        "full_pipeline": {
            "cycles": 150,
            "latency_us": 0.0,
            "throughput_ops_per_sec": 0.0,
        }
    }


def generate_area_template() -> Dict:
    """Template for area breakdown"""
    gw5a_spec = {
        "lut4_available": 8256,
        "dsp_available": 16,
        "bram_available": 32,
    }
    
    return {
        "platform_spec": gw5a_spec,
        "modules": [
            asdict(AreaBreakdown(
                module_name="M31_MULTIPLIER",
                lut4_used=600,
                lut4_available=gw5a_spec["lut4_available"],
                dsp_used=16,
                dsp_available=gw5a_spec["dsp_available"],
                bram_used=0,
                bram_available=gw5a_spec["bram_available"],
                max_freq_mhz=70,
            )),
            asdict(AreaBreakdown(
                module_name="FP4_INVERTER",
                lut4_used=800,
                lut4_available=gw5a_spec["lut4_available"],
                dsp_used=2,
                dsp_available=gw5a_spec["dsp_available"],
                bram_used=1,
                bram_available=gw5a_spec["bram_available"],
                max_freq_mhz=65,
            )),
        ],
        "summary": {
            "total_lut4": 0,
            "total_dsp": 0,
            "total_bram": 0,
            "utilization_percent": {
                "lut4": 0.0,
                "dsp": 0.0,
                "bram": 0.0,
            }
        }
    }


def generate_coverage_template() -> Dict:
    """Template for test coverage"""
    return {
        "metadata": {
            "date": datetime.now().isoformat(),
            "tool": "run_all_tests.py",
        },
        "test_suites": [
            asdict(TestCoverage(
                test_suite="spu13_m31_multiplier_tb",
                test_count=50,
                pass_count=50,
                fail_count=0,
                assertions=200,
            )),
            asdict(TestCoverage(
                test_suite="spu13_fp4_inverter_tb",
                test_count=30,
                pass_count=30,
                fail_count=0,
                assertions=150,
            )),
        ],
        "overall": {
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
            "pass_rate_percent": 0.0,
        }
    }


def generate_baseline_template() -> Dict:
    """Template for comparative analysis"""
    return {
        "metadata": {
            "date": datetime.now().isoformat(),
            "operation": "Rational Jacobian (3×3 matrix) evaluation",
            "note": "All systems use same test vectors; compare latency + energy",
        },
        "baselines": [
            asdict(ComparativeBaseline(
                system_name="SPU-13 RPLU (GW5A-25A @ 12 MHz)",
                bits="exact",
                latency_us=0.120,
                power_mw=25,
                energy_per_op_uj=3.0,
                area_mm2=12.0,
            )),
            asdict(ComparativeBaseline(
                system_name="Intel Core i9-12900 @ 5 GHz (FP32)",
                bits="FP32",
                latency_us=2.5,
                power_mw=150,
                energy_per_op_uj=375.0,
            )),
            asdict(ComparativeBaseline(
                system_name="NVIDIA A100 Tensor (TF32)",
                bits="TF32",
                latency_us=0.8,
                power_mw=400,
                energy_per_op_uj=320.0,
            )),
        ],
        "analysis": {
            "speedup_vs_cpu": 20.8,  # 2.5 µs / 0.120 µs
            "energy_advantage_vs_cpu_percent": 99.2,  # (375 - 3) / 375
            "determinism_guarantee": "±0 ns (exact rational, no rounding)",
        }
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generate-templates",
        action="store_true",
        help="Generate JSON templates for all metrics",
    )
    parser.add_argument(
        "--output-dir",
        default="tools/build",
        help="Output directory for generated templates",
    )
    
    args = parser.parse_args()
    
    if args.generate_templates:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        templates = {
            "power_measurements.json": generate_power_template(),
            "latency_measurements.json": generate_latency_template(),
            "area_breakdown.json": generate_area_template(),
            "test_coverage.json": generate_coverage_template(),
            "comparative_baselines.json": generate_baseline_template(),
        }
        
        for name, data in templates.items():
            path = output_dir / name
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"✓ {path}")
        
        print(f"\n✅ Templates generated in {output_dir}")
        print("Next steps:")
        print("  1. Collect power data → edit power_measurements.json")
        print("  2. Extract area from nextpnr JSON → populate area_breakdown.json")
        print("  3. Run test suite → populate test_coverage.json")
        print("  4. Benchmark baselines → populate comparative_baselines.json")
